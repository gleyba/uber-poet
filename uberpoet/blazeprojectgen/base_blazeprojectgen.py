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

from abc import ABC, abstractmethod
from os.path import basename, dirname, join

from uberpoet import locreader
from uberpoet.filegen import Language, FileResult, ProgressReporter
from uberpoet.loccalc import LOCCalculator
from uberpoet.moduletree import ModuleNode
from uberpoet.util import first_in_dict, first_key, makedir


class Generator(ABC):
    loc_calc = LOCCalculator()

    def __init__(self, language: Language, sample_file: FileResult):
        super().__init__()
        self.language = language
        self.file_size_loc = Generator.loc_calc.calculate_loc(
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
    def generate_souces(self) -> dict[str, FileResult]:
        pass


class BaseBlazeProjectGenerator(ABC):
    DIR_NAME = dirname(__file__)
    RESOURCE_DIR = join(DIR_NAME, "../resources")

    def __init__(
        self,
        app_root: str,
        blaze_app_root: str,
        bzl_lib_template: str,
        bzl_app_template: str,
        main_template: str,
        main_language: Language,
        generators: list[Generator],
        main_file_name: str,
        build_file_name: str,
        src_dir_name: str,
        resources: dict[str, str],
        resource_dirs: dict[str, str],
        reporter: ProgressReporter,
    ):
        self.app_root = app_root
        self.blaze_app_root = blaze_app_root
        self.bzl_lib_template = self.load_resource(bzl_lib_template)
        self.bzl_app_template = self.load_resource(bzl_app_template)
        self.main_template = self.load_resource(main_template)
        self.main_language = main_language
        self.generators = {g.language: g for g in generators}
        self.main_file_name = main_file_name
        self.build_file_name = build_file_name
        self.src_dir_name = src_dir_name
        self.resources = resources
        self.resource_dirs = resource_dirs
        self.reporter = reporter

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

    # Generation Functions
    def gen_app(
        self,
        app_node: ModuleNode,
        node_list: list[ModuleNode],
        lang_loc: dict[Language, int],
        loc_json_file_path: str,
    ):
        library_node_list = [n for n in node_list if n.node_type == ModuleNode.LIBRARY]

        if loc_json_file_path:
            loc_reader = locreader.LocFileReader()
            loc_reader.read_loc_file(loc_json_file_path)
            module_index = {}
            for n in library_node_list:
                loc = loc_reader.loc_for_module(n.name)
                language = loc_reader.language_for_module(n.name)
                files = self.gen_lib_module(module_index, n, loc, language)
                module_index[n.name] = {
                    "files": files,
                    "loc": loc,
                    "language": language,
                }
        else:
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

            module_index = {}
            for idx, n in enumerate(library_node_list):
                for cur_language, max_index in max_lang_index.items():
                    language = cur_language
                    if idx < max_index:
                        break

                files = self.gen_lib_module(module_index, n, loc_per_unit, language)
                module_index[n.name] = {
                    "files": files,
                    "loc": loc_per_unit,
                    "language": language,
                }

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

        if loc_json_file_path:
            # Copy the LOC file into the generated project.
            shutil.copyfile(
                loc_json_file_path, join(self.app_root, basename(loc_json_file_path))
            )

        serializable_module_index = {
            key: {"file_count": len(value["files"]), "loc": value["loc"]}
            for key, value in module_index.items()
        }

        with open(
            join(self.app_root, "module_index.json"), "w"
        ) as module_index_json_file:
            json.dump(serializable_module_index, module_index_json_file)

    def gen_app_build(self, app_node: ModuleNode):
        module_dep_list = self.make_dep_list([i.name for i in app_node.deps])
        return self.bzl_app_template.format(
            deps=module_dep_list,
            **self.app_build_kwargs(),
        )

    def gen_app_main(self, app_node: ModuleNode, module_index: int):
        importing_module_name = app_node.deps[0].name
        file_index = first_in_dict(module_index[importing_module_name]["files"])
        language = module_index[importing_module_name]["language"]
        class_key = first_key(file_index.classes)
        class_index = first_in_dict(file_index.classes)
        function_key = first_in_dict(class_index)[0]
        return self.generators[self.main_language].gen_main(
            self.main_template,
            importing_module_name,
            class_key,
            function_key,
            language,
        )

    # Library Generation
    def gen_lib_module(
        self,
        module_index: dict[str, dict],
        module_node: ModuleNode,
        loc_per_unit: int,
        language: Language,
    ):
        deps = self.make_dep_list([i.name for i in module_node.deps])
        build_text = self.bzl_lib_template.format(
            module_node.name,
            deps=deps,
            **self.lib_build_kwargs(),
        )
        # We now return a topologically sorted list of the graph which means that we will already have the
        # deps of a module inside the module index before we process this one.  This allows us to reach into
        # the generated sources for the dependencies in order to create an instance of their class and
        # invoke their functions.
        deps_from_index = [{n.name: module_index[n.name]} for n in module_node.deps]

        # Make Text
        gen = self.generators[language]
        file_count = gen.get_file_count(loc_per_unit, module_node)
        files = gen.generate_souces(file_count, deps_from_index)

        # Make Module Directories
        module_dir_path = join(self.app_root, module_node.name)
        files_dir_path = join(module_dir_path, self.src_dir_name)
        makedir(module_dir_path)
        makedir(files_dir_path)

        # Write BUCK or BUILD Files
        build_path = join(module_dir_path, self.build_file_name)
        self.write_file(build_path, build_text)

        # Write Swift Files
        for file_name, file_obj in files.items():
            file_path = join(files_dir_path, file_name)
            self.write_file(file_path, file_obj.text)
            if self.reporter:
                self.reporter.report_progress(file_obj.language, file_obj.text_line_count)
            file_obj.text = ""  # Save memory after write

        module_node.extra_info = files

        return files
