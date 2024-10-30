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

from os.path import dirname, join

from uberpoet.filegen import (
    FileResult,
    Language,
    ObjCHeaderFileGenerator,
    ObjCSourceFileGenerator,
    SwiftFileGenerator,
)
from uberpoet.moduletree import ModuleNode

from .base_blazeprojectgen import BaseBlazeProjectGenerator, Generator


class SwiftGenerator(Generator):
    def __init__(self):
        self.swift_gen = SwiftFileGenerator()
        super().__init__(Language.SWIFT, self.swift_gen.gen_file(3, 3))

    def generate_souces(
        self, file_count: int, deps_from_index: list[dict[str, ModuleNode]]
    ) -> dict[str, FileResult]:
        return {
            "File{}.swift".format(i): self.swift_gen.gen_file(3, 3, deps_from_index)
            for i in range(file_count)
        }


class ObjCGenerator(Generator):
    def __init__(self):
        self.objc_source_gen = ObjCSourceFileGenerator()
        self.objc_header_gen = ObjCHeaderFileGenerator()
        super().__init__(Language.OBJC, self.objc_source_gen.gen_file(3, 3))

    def generate_souces(
        self, file_count: int, deps_from_index: list[dict[str, ModuleNode]]
    ) -> dict[str, FileResult]:
        files = {}
        for i in range(file_count):
            objc_source_file = self.objc_source_gen.gen_file(
                3, 3, import_list=deps_from_index + ["File{}.h".format(i)]
            )
            files["File{}.m".format(i)] = objc_source_file
            files["File{}.h".format(i)] = self.objc_header_gen.gen_file(
                objc_source_file
            )
        return files


class IosBlazeProjectGenerator(BaseBlazeProjectGenerator):
    BazelResources = {
        "Info.plist": "App/Info.plist",
        "mockbazelworkspace": "WORKSPACE.bazel",
    }
    BazelResourceDirs = {
        "tools": "tools",
    }
    BuckResouces = {
        "Info.plist": "App/Info.plist",
        "mockbuckconfig": ".buckconfig",
    }
    BuckResourceDirs = {}

    def __init__(self, app_root, blaze_app_root, use_wmo=False, flavor="buck"):
        super().__init__(
            app_root=app_root,
            blaze_app_root=blaze_app_root,
            bzl_lib_template="mock_{}_ios_libtemplate.bzl".format(flavor),
            bzl_app_template="mock_{}_ios_apptemplate.bzl".format(flavor),
            main_template="mock_ios_appdelegate",
            main_language=Language.SWIFT,
            generators=[SwiftGenerator(), ObjCGenerator()],
            main_file_name="AppDelegate.swift",
            build_file_name="BUCK" if flavor == "buck" else "BUILD.bazel",
            src_dir_name="Sources",
            resources=IosBlazeProjectGenerator.BuckResouces
            if flavor == "buck"
            else IosBlazeProjectGenerator.BazelResources,
            resource_dirs=IosBlazeProjectGenerator.BuckResourceDirs
            if flavor == "buck"
            else IosBlazeProjectGenerator.BazelResourceDirs,
        )

        self.use_wmo = use_wmo
        self.flavor = flavor

    def example_command(self):
        if self.flavor == "buck":
            return "buck project //App:App"
        elif self.flavor == "bazel":
            return "Use Tulsi or XCHammer to generate an Xcode project."

    def gen_app(
        self, app_node, node_list, target_swift_loc, target_objc_loc, loc_json_file_path
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
