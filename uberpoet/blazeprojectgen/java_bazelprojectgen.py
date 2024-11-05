#  Copyright (c) 2024 Kolobkov Tech Consulting LLC.
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

from .base_blazeprojectgen import (
    BaseBlazeProjectGenerator,
    LanguageGenerator,
)
from uberpoet.filegen import (
    FileResult,
    Language,
    JavaFileGenerator,
)
from uberpoet.filegen import (
    ModuleResult,
    ProgressReporter,
)
from uberpoet.moduletree import ModuleNode
from uberpoet.commandlineutil import JavaAppGenerationConfig


class JavaGenerator(LanguageGenerator):
    def __init__(self, main_template: str, java_package: str):
        self.java_gen = JavaFileGenerator(
            main_template,
            java_package,
        )
        super().__init__(
            Language.JAVA,
            self.java_gen.gen_file("test", "dummy", 3, 3, []),
        )
        self.gen_main = self.java_gen.gen_main

    def generate_sources(
        self,
        file_count: int,
        module_node: ModuleNode,
        deps_from_index: list[ModuleResult],
    ) -> Generator[FileResult, None, None]:
        for i in range(file_count):
            yield self.java_gen.gen_file(
                module_node.name,
                "File{}.java".format(i),
                3,
                3,
                deps_from_index,
            )
        return


class JavaBlazeProjectGenerator(BaseBlazeProjectGenerator):
    def __init__(
        self, config: JavaAppGenerationConfig, reporter: ProgressReporter = None
    ):
        super().__init__(
            config=config,
            bzl_lib_template="java/mock_bazel_libtemplate.bzl",
            bzl_app_template="java/mock_bazel_apptemplate.bzl",
            main_language=Language.JAVA,
            generators=[
                JavaGenerator(
                    self.load_resource("java/mock_main_template.java"),
                    config.java_package,
                ),
            ],
            main_file_name="App.java",
            build_file_name="BUILD.bazel",
            src_dir_name="src",
            resources={
                "java/mock_module_bazel": "MODULE.bazel",
            },
            resource_dirs={},
            reporter=reporter,
        )

    def example_command(self) -> str:
        return ""

    def app_build_kwargs(self) -> dict[str, str]:
        return {
            "package": self.config.java_package,
        }

    def lib_build_kwargs(self) -> dict[str, str]:
        return {}
