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

from typing import Generator
from os.path import basename, join
import shutil

from uberpoet import locreader
from uberpoet.filegen import (
    FileResult,
    Language,
    ObjCHeaderFileGenerator,
    ObjCSourceFileGenerator,
    SwiftFileGenerator,
)
from uberpoet.commandlineutil import BaseAppGenerationConfig
from uberpoet.filegen import ModuleResult, ProgressReporter
from uberpoet.moduletree import ModuleNode

from .base_blazeprojectgen import BaseBlazeProjectGenerator, LanguageGenerator


class SwiftGenerator(LanguageGenerator):
    def __init__(self, main_template: str):
        self.swift_gen = SwiftFileGenerator(main_template)
        self.gen_main = self.swift_gen.gen_main
        super().__init__(
            Language.SWIFT,
            self.swift_gen.gen_file("dummy", 3, 3, []),
        )

    def generate_sources(
        self,
        file_count: int,
        _: ModuleNode,
        deps_modules: list[ModuleResult],
    ) -> Generator[FileResult, None, None]:
        for i in range(file_count):
            yield self.swift_gen.gen_file(
                "File{}.swift".format(i),
                3,
                3,
                deps_modules,
            )
        return


class ObjCGenerator(LanguageGenerator):
    def __init__(self):
        self.objc_source_gen = ObjCSourceFileGenerator()
        self.objc_header_gen = ObjCHeaderFileGenerator()
        super().__init__(
            Language.OBJC,
            self.objc_source_gen.gen_file("dummy", 3, 3, []),
        )

    def generate_sources(
        self,
        file_count: int,
        _: ModuleNode,
        deps_modules: list[ModuleResult],
    ) -> Generator[FileResult, None, None]:
        for i in range(file_count):
            objc_source_file = self.objc_source_gen.gen_file(
                "File{}.m".format(i),
                3,
                3,
                deps_modules + ["File{}.h".format(i)],
            )
            yield objc_source_file
            yield self.objc_header_gen.gen_file(
                "File{}.h".format(i),
                objc_source_file,
            )
        return


class IosBlazeProjectGenerator(BaseBlazeProjectGenerator):
    BazelResources = {
        "ios/Info.plist": "App/Info.plist",
        "ios/mock_bazel_workspace": "WORKSPACE.bazel",
    }
    BazelResourceDirs = {
        "tools": "tools",
    }
    BuckResouces = {
        "ios/Info.plist": "App/Info.plist",
        "ios/mock_buck_config": ".buckconfig",
    }
    BuckResourceDirs = {}

    def __init__(
        self,
        config: BaseAppGenerationConfig,
        use_wmo=False,
        flavor="buck",
        reporter: ProgressReporter = None,
    ):
        super().__init__(
            config=config,
            bzl_lib_template="ios/mock_{}_libtemplate.bzl".format(flavor),
            bzl_app_template="ios/mock_{}_apptemplate.bzl".format(flavor),
            main_language=Language.SWIFT,
            generators=[
                SwiftGenerator(self.load_resource("ios/mock_appdelegate")),
                ObjCGenerator(),
            ],
            main_file_name="AppDelegate.swift",
            build_file_name="BUCK" if flavor == "buck" else "BUILD.bazel",
            src_dir_name="Sources",
            resources=IosBlazeProjectGenerator.BuckResouces
            if flavor == "buck"
            else IosBlazeProjectGenerator.BazelResources,
            resource_dirs=IosBlazeProjectGenerator.BuckResourceDirs
            if flavor == "buck"
            else IosBlazeProjectGenerator.BazelResourceDirs,
            reporter=reporter,
        )
        self.use_wmo = use_wmo
        self.flavor = flavor

    def example_command(self):
        if self.flavor == "buck":
            return "buck project //App:App"
        elif self.flavor == "bazel":
            return "Use Tulsi or XCHammer to generate an Xcode project."

    def gen_ios_app(
        self,
        app_node: ModuleNode,
        node_list: list[ModuleNode],
        target_swift_loc: int,
        target_objc_loc: int,
        loc_json_file_path: str,
    ):
        if loc_json_file_path:
            library_node_list = [
                n for n in node_list if n.node_type == ModuleNode.LIBRARY
            ]
            loc_reader = locreader.LocFileReader()
            loc_reader.read_loc_file(loc_json_file_path)
            module_index = {}
            for n in library_node_list:
                loc = loc_reader.loc_for_module(n.name)
                language = loc_reader.language_for_module(n.name)
                files = self.gen_lib_module(module_index, n, loc, language)
                module_index[n.name] = ModuleResult(
                    name=n.name,
                    files=files,
                    loc=loc,
                    language=language,
                )

            self.gen_app_from_module_index(app_node, module_index)

            # Copy the LOC file into the generated project.
            shutil.copyfile(
                loc_json_file_path,
                join(self.app_root, basename(loc_json_file_path)),
            )
        else:
            super().gen_app(
                app_node,
                node_list,
                {
                    Language.SWIFT: target_swift_loc,
                    Language.OBJC: target_objc_loc,
                },
            )

    def app_build_kwargs(self) -> dict[str, str]:
        return {"wmo": "YES" if self.use_wmo else "NO"}

    def lib_build_kwargs(self) -> dict[str, str]:
        return {"wmo": "YES" if self.use_wmo else "NO"}
