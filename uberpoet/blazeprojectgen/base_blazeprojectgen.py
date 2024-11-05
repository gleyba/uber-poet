#  Copyright (c) 2018 Uber Technologies, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from __future__ import absolute_import

import json
import math
import shutil

import concurrent.futures
from abc import ABC, abstractmethod
from os.path import dirname, join
from typing import Generator
from threading import Lock

from uberpoet import locreader
from uberpoet.commandlineutil import BaseAppGenerationConfig
from uberpoet.filegen import Language, FileResult, ModuleResult, ProgressReporter
from uberpoet.loccalc import LOCCalculator
from uberpoet.moduletree import ModuleNode
from uberpoet.util import makedir


class LanguageGenerator(ABC):
    loc_calc = LOCCalculator()

    def __init__(self, language: Language, sample_file: FileResult):
        super().__init__()
        self.language = language
        self.file_size_loc = LanguageGenerator.loc_calc.calculate_loc(
            sample_file.text, language
        )

    def get_file_count(self, loc_per_unit: int, module_node: ModuleNode) -> int:
        file_count = (
            max(self.file_size_loc, loc_per_unit) * module_node.code_units
        ) / self.file_size_loc
        if file_count < 1:
            raise ValueError(
                "Lines of code count is too small for the module {} to fit one file, increase it.".format(
                    module_node.name
                )
            )
        return int(file_count)

    @abstractmethod
    def generate_sources(
        self, file_count: int, deps_from_index: list[ModuleResult]
    ) -> Generator[FileResult, None, None]:
        pass


class BaseBlazeProjectGenerator(ABC):
    DIR_NAME = dirname(__file__)
    RESOURCE_DIR = join(DIR_NAME, "../resources")

    def __init__(
        self,
        config: BaseAppGenerationConfig,
        bzl_lib_template: str,
        bzl_app_template: str,
        main_language: Language,
        generators: list[LanguageGenerator],
        main_file_name: str,
        build_file_name: str,
        src_dir_name: str,
        resources: dict[str, str],
        resource_dirs: dict[str, str],
        reporter: ProgressReporter,
    ):
        self.app_root = config.output_directory
        self.bzl_lib_template = self.load_resource(bzl_lib_template)
        self.bzl_app_template = self.load_resource(bzl_app_template)
        self.main_language = main_language
        self.generators = {g.language: g for g in generators}
        self.main_file_name = main_file_name
        self.build_file_name = build_file_name
        self.src_dir_name = src_dir_name
        self.resources = resources
        self.resource_dirs = resource_dirs
        self.reporter = reporter
        self.concurrency = config.concurrency

    @staticmethod
    def load_resource(name):
        with open(join(BaseBlazeProjectGenerator.RESOURCE_DIR, name), "r") as f:
            return f.read()

    @staticmethod
    def copy_resource(name, dest):
        origin = join(BaseBlazeProjectGenerator.RESOURCE_DIR, name)
        shutil.copyfile(origin, dest)

    @staticmethod
    def copy_resource_dir(name, dest):
        origin = join(BaseBlazeProjectGenerator.RESOURCE_DIR, name)
        shutil.copytree(origin, dest)

    @staticmethod
    def write_file(path, text):
        with open(path, "w") as f:
            f.write(text)

    @staticmethod
    def make_list_str(items):
        return (",\n" + (" " * 8)).join(items)

    def make_dep_list(self, items):
        return self.make_list_str(["'//{0}:{0}'".format(i) for i in items])

    @abstractmethod
    def example_command(self) -> str:
        pass

    @abstractmethod
    def app_build_kwargs(self) -> dict[str, str]:
        return {}

    @abstractmethod
    def lib_build_kwargs(self) -> dict[str, str]:
        return {}

    def gen_app_from_module_index(
        self, app_node: ModuleNode, module_index: dict[str, ModuleResult]
    ):
        app_module_dir = join(self.app_root, "App")
        makedir(app_module_dir)

        app_files = {
            self.main_file_name: self.gen_app_main(app_node, module_index),
            self.build_file_name: self.gen_app_build(app_node),
        }

        for resource, target in self.resources.items():
            self.copy_resource(resource, join(self.app_root, target))

        for resource_dir, target in self.resource_dirs.items():
            self.copy_resource_dir(resource_dir, join(self.app_root, target))

        for name, text in app_files.items():
            self.write_file(join(app_module_dir, name), text)

        serializable_module_index = {
            key: {"file_count": len(value.files), "loc": value.loc}
            for key, value in module_index.items()
        }

        with open(
            join(self.app_root, "module_index.json"), "w"
        ) as module_index_json_file:
            json.dump(serializable_module_index, module_index_json_file)

    # Generation Functions
    def gen_app(
        self,
        app_node: ModuleNode,
        node_list: list[ModuleNode],
        lang_loc: dict[Language, int],
    ):
        library_node_list = [n for n in node_list if n.node_type == ModuleNode.LIBRARY]

        total_code_units = 0
        for l in library_node_list:
            total_code_units += l.code_units

        total_loc = sum(lang_loc.values())
        module_count_percentage = {
            language: round(float(loc) / total_loc, 2)
            for language, loc in lang_loc.items()
        }
        loc_per_unit = total_loc / total_code_units
        max_lang_index = {
            language: math.ceil((len(library_node_list) * percentage))
            for language, percentage in module_count_percentage.items()
        }

        with concurrent.futures.ThreadPoolExecutor(
            max_workers=self.concurrency
        ) as executor:
            module_index_futures = {}
            module_index_futures_lock = Lock()

            def gen_module(idx, module):
                nonlocal module_index_futures
                nonlocal module_index_futures_lock
                language = None
                for cur_language, max_index in max_lang_index.items():
                    language = cur_language
                    if idx < max_index:
                        break

                with module_index_futures_lock:
                    deps_futures = [
                        module_index_futures.get(dep.name) for dep in module.deps
                    ]

                deps = [d.result() for d in deps_futures]

                files = self.gen_lib_module(module, deps, loc_per_unit, language)

                return ModuleResult(
                    name=module.name,
                    files=files,
                    loc=loc_per_unit,
                    language=language,
                )

            # We now return a topologically sorted list of the graph which means that we will already have the
            # deps of a module inside the module index before we process this one.  This allows us to reach into
            # the generated sources for the dependencies in order to create an instance of their class and
            # invoke their functions.
            with module_index_futures_lock:
                module_index_futures = {
                    node.name: executor.submit(gen_module, idx, node)
                    for idx, node in enumerate(library_node_list)
                }

            concurrent.futures.wait(module_index_futures.values())
            module_index = {
                name: module_future.result()
                for name, module_future in module_index_futures.items()
            }

        self.gen_app_from_module_index(app_node, module_index)

    def gen_app_build(self, app_node: ModuleNode):
        module_dep_list = self.make_dep_list([i.name for i in app_node.deps])
        return self.bzl_app_template.format(
            deps=module_dep_list,
            **self.app_build_kwargs(),
        )

    def gen_app_main(self, app_node: ModuleNode, module_index: dict[str, ModuleResult]):
        importing_module = app_node.deps[0]
        module_result = module_index[importing_module.name]
        return self.generators[self.main_language].gen_main(module_result)

    # Library Generation
    def gen_lib_module(
        self,
        module_node: ModuleNode,
        dep_modules: list[ModuleResult],
        loc_per_unit: int,
        language: Language,
    ) -> dict[str, FileResult]:
        deps = self.make_dep_list([i.name for i in module_node.deps])
        build_text = self.bzl_lib_template.format(
            name=module_node.name,
            deps=deps,
            **self.lib_build_kwargs(),
        )

        # Make Text
        gen = self.generators[language]
        file_count = gen.get_file_count(loc_per_unit, module_node)

        # Make Module Directories
        module_dir_path = join(self.app_root, module_node.name)
        files_dir_path = join(module_dir_path, self.src_dir_name)
        makedir(module_dir_path)
        makedir(files_dir_path)

        # Write BUCK or BUILD Files
        build_path = join(module_dir_path, self.build_file_name)
        self.write_file(build_path, build_text)

        # Write Swift Files
        module_node.extra_info = {}
        for file_obj in gen.generate_sources(file_count, module_node, dep_modules):
            file_path = join(files_dir_path, file_obj.filename)
            self.write_file(file_path, file_obj.text)
            if self.reporter:
                self.reporter.report_progress(
                    file_obj.language,
                    file_obj.text_line_count,
                )
            file_obj.text = ""  # Save memory after write
            module_node.extra_info[file_obj.filename] = file_obj

        return module_node.extra_info
