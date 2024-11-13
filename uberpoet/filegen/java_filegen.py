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

from uberpoet.util import seed

from .filegen import *
from .imports_selector import (
    ClassKey,
    ImportsSelector,
)

java_inner_func_call_template = (
    """{0}new File{1}.MyClass{2}().complexCrap{3}(1, 3){4}"""
)
java_external_func_call_template = """{0}new MyClass{1}().complexCrap{2}(4, 2){3}"""

java_func_template = """
public int complexCrap{0}(int arg, Object stuff) {{
    int a = (int) (4 * {1} + (float) arg / 32.0);
    int b = (int) (4 * {1} + (float) arg / 32.0);
    int c = (int) (4 * {1} + (float) arg / 32.0);
    return (int)(4 * {1} + arg / 32.0) + a + b + c;
}}"""

java_class_template = """
    public static class MyClass{0} {{
    
        public int x;
        public String y;
    
        public MyClass{0} () {{
            x = 7;
            y = "hi";
{2}
        }}
    
        {1}
    }}"""


class JavaFileGenerator(FileGenerator):
    def __init__(self, main_template: str, java_package: str):
        super().__init__()
        self.main_template = main_template
        self.java_package = java_package

    @staticmethod
    def gen_func(
        functions: list[int],
        var_name: str,
        indent=0,
    ) -> list[str]:
        out = []

        for num in functions:
            text = java_func_template.format(num, var_name)
            indented_text = "\n".join(" " * indent + line for line in text.splitlines())
            out.append(indented_text)

        return out

    def gen_class(
        self,
        file_spec: FileSpec,
        imports_selector: ImportsSelector,
    ) -> tuple[list[str], set[str]]:
        out = []
        external_imports = set()

        for class_spec in file_spec.classes:
            num = class_spec.key
            func_out = self.gen_func(
                class_spec.func_keys,
                "x",
                indent=8,
            )
            func_call_out = []
            caller_key = ClassKey(file_spec.file_idx, class_spec.key)
            inner_imports_result = imports_selector.get_inner_imports(caller_key)
            for file_idx, class_imports in inner_imports_result.file_to_classes.items():
                for class_idx, funcs in class_imports.class_to_functions.items():
                    for func_idx in funcs:
                        func_call_out.append(
                            java_inner_func_call_template.format(
                                " " * 12,
                                file_idx,
                                class_idx,
                                func_idx,
                                ";",
                            )
                        )
            external_imports_result = imports_selector.get_external_imports()
            for (
                module_name,
                inner_imports,
            ) in external_imports_result.module_to_inner_imports.items():
                for file_idx, class_imports in inner_imports.file_to_classes.items():
                    for class_idx, funcs in class_imports.class_to_functions.items():
                        external_imports.add(
                            "{}.File{}.MyClass{}".format(
                                module_name,
                                file_idx,
                                class_idx,
                            )
                        )
                        for func_idx in funcs:
                            func_call_out.append(
                                java_external_func_call_template.format(
                                    " " * 12,
                                    class_idx,
                                    func_idx,
                                    ";",
                                )
                            )

            out.append(
                java_class_template.format(
                    num,
                    "\n".join(func_out),
                    "\n".join(func_call_out),
                )
            )

        return out, external_imports

    def gen_file(
        self,
        module_name: str,
        file_spec: FileSpec,
        imports: ImportsSelector,
    ) -> FileResult:
        external_imports = imports.get_external_imports()

        funcs_out = self.gen_func([seed() for _ in range(3)], "7", 4)
        class_out, external_imports = self.gen_class(file_spec, imports)
        chunks = (
            [
                uber_poet_header,
                "package {}.{};\n".format(
                    self.java_package,
                    module_name,
                ),
            ]
            + [
                "import {}.{};".format(
                    self.java_package,
                    import_str,
                )
                for import_str in external_imports
            ]
            + [
                "public class File{} {{".format(file_spec.file_idx),
            ]
            + funcs_out
            + class_out
            + [
                "}",
            ]
        )

        return FileResult(
            "File{}.java".format(file_spec.file_idx),
            Language.JAVA,
            "\n".join(chunks),
            file_spec,
        )

    def gen_main(self, module_result: ModuleResult):
        file = module_result.first_file()
        class_num, func_num = file.first_class_and_func()
        action_expr = java_external_func_call_template.format(
            "",
            class_num,
            func_num,
            "",
        )
        imports = "import {}.{}.{}.MyClass{};".format(
            self.java_package,
            module_result.name,
            file.basename(),
            class_num,
        )
        body = "System.out.println({});".format(action_expr)
        return self.main_template.format(
            header=uber_poet_header,
            imports=imports,
            package=self.java_package,
            body=body,
        )
