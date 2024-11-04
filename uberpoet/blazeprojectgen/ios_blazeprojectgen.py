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
        self, file_count: int, deps_from_index: list[ModuleResult]
    ) -> Generator[FileResult, None, None]:
        for i in range(file_count):
            yield self.swift_gen.gen_file(
                "File{}.swift".format(i),
                3,
                3,
                deps_from_index,
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
        self, file_count: int, deps_from_index: list[ModuleResult]
    ) -> Generator[FileResult, None, None]:
        for i in range(file_count):
            objc_source_file = self.objc_source_gen.gen_file(
                "File{}.m".format(i),
                3,
                3,
                deps_from_index + ["File{}.h".format(i)],
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

    def gen_app(
        self,
        app_node: ModuleNode,
        node_list: list[ModuleNode],
        target_swift_loc: int,
        target_objc_loc: int,
        loc_json_file_path: str,
    ):
        super().gen_app(
            app_node,
            node_list,
            {Language.SWIFT: target_swift_loc, Language.OBJC: target_objc_loc},
            loc_json_file_path,
        )

    def app_build_kwargs(self) -> dict[str, str]:
        return {"wmo": "YES" if self.use_wmo else "NO"}

    def lib_build_kwargs(self) -> dict[str, str]:
        return {"wmo": "YES" if self.use_wmo else "NO"}
