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
from copy import deepcopy

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
    FileSpec,
    ModuleResult,
    ProgressReporter,
)
from uberpoet.filegen.imports_selector import (
    ImportsSelectorImpl,
    ImportsSelectorDummy,
)

from uberpoet.moduletree import ModuleNode
from uberpoet.commandlineutil import JavaAppGenerationConfig


class JavaGenerator(LanguageGenerator):
    def __init__(
        self,
        main_template: str,
        java_package: str,
        class_per_file_count=3,
        func_per_class_count=3,
        inner_imports_count=12,
        external_imports_count=48,
    ):
        self.java_gen = JavaFileGenerator(
            main_template,
            java_package,
        )
        self.class_count = class_per_file_count
        self.func_count = func_per_class_count
        self.inner_imports_count = inner_imports_count
        self.external_imports_count = external_imports_count
        super().__init__(
            Language.JAVA,
            self.java_gen.gen_file(
                "test",
                FileSpec.new_with_seed(
                    0,
                    class_per_file_count,
                    func_per_class_count,
                ),
                ImportsSelectorDummy(
                    inner_imports_count,
                    external_imports_count,
                ),
            ),
        )
        self.gen_main = self.java_gen.gen_main

    def generate_sources(
        self,
        file_count: int,
        module_node: ModuleNode,
        deps_modules: list[ModuleResult],
    ) -> Generator[FileResult, None, None]:
        file_specs = [
            FileSpec.new_with_seed(
                file_idx,
                self.class_count,
                self.func_count,
            )
            for file_idx in range(file_count)
        ]

        imports_selector = ImportsSelectorImpl(
            deepcopy(file_specs),
            self.inner_imports_count,
            deepcopy(deps_modules),
            self.external_imports_count,
        )

        for file_spec in file_specs:
            yield self.java_gen.gen_file(
                module_node.name,
                file_spec,
                imports_selector,
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
