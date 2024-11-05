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

java_func_call_template = """{0}.MyClass{1}.complexCrap{2}(4, 2)"""

java_func_template = """
public int complexCrap{0}(int arg, Object stuff) {{
    int a = (int) (4 * {1} + (float) arg / 32.0);
    int b = (int) (4 * {1} + (float) arg / 32.0);
    int c = (int) (4 * {1} + (float) arg / 32.0);
    return (int)(4 * {1} + arg / 32.0) + a + b + c;
}}"""

java_class_template = """
public class Myclass{0} {{

    public int x;
    public String y;

    public Myclass{0} () {{
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
    def gen_func(function_count, var_name, indent=0):
        out = []
        nums = []

        for _ in range(function_count):
            num = seed()
            text = java_func_template.format(num, var_name)
            indented_text = "\n".join(" " * indent + line for line in text.splitlines())
            nums.append(num)
            out.append(indented_text)

        return "\n".join(out), nums

    def get_import_func_calls(self, import_list: list[ModuleResult | str], indent=0):
        out = []
        for module in import_list:
            if type(module) is str:
                continue

            for file_result in module.files.values():
                for class_num, func_nums in file_result.classes.items():
                    for func_num in func_nums:
                        text = java_func_call_template.format(
                            "%s.%s"
                            % (
                                module.name,
                                file_result.filename,
                            ),
                            class_num,
                            func_num,
                        )
                        indented_text = "\n".join(
                            " " * indent + line for line in text.splitlines()
                        )
                        out.append(indented_text)

        return "\n".join(out)

    def gen_class(
        self,
        class_count: int,
        func_per_class_count: int,
        import_list: list[ModuleResult | str],
    ) -> str:
        out = []
        class_nums = {}

        for _ in range(class_count):
            num = seed()
            func_out, func_nums = self.gen_func(
                func_per_class_count,
                "x",
                indent=8,
            )
            func_call_out = self.get_import_func_calls(
                import_list,
                indent=12,
            )
            out.append(
                java_class_template.format(
                    num,
                    func_out,
                    func_call_out,
                )
            )

            class_nums[num] = func_nums

        return "\n".join(out), class_nums

    def gen_file(
        self,
        module_name: str,
        file_name: str,
        class_count: int,
        function_count: int,
        import_list: list[ModuleResult | str],
    ) -> FileResult:
        if import_list is None:
            import_list = []

        package_out = "package {}.{};".format(
            self.java_package,
            module_name,
        )

        imports_out = "\n".join(
            [
                "import {}.{};".format(
                    self.java_package, i if type(i) is str else i.name
                )
                for i in import_list
            ]
        )

        class_start_out = "public class {} {{".format(file_name)

        func_out, func_nums = self.gen_func(function_count, "7", 4)
        class_out, class_nums = self.gen_class(class_count, 5, import_list)

        class_end_out = "}"

        chunks = [
            uber_poet_header,
            package_out,
            imports_out,
            class_start_out,
            func_out,
            class_out,
            class_end_out,
        ]

        return FileResult(
            file_name,
            Language.JAVA,
            "\n".join(chunks),
            func_nums,
            class_nums,
        )

    def gen_main(self, module_result: ModuleResult):
        file = module_result.first_file()
        class_num, func_num = file.first_class_and_func()
        action_expr = java_func_call_template.format(
            file.filename,
            class_num,
            func_num,
        )
        return self.main_template.format(
            header=uber_poet_header,
            imports="import {}.{}.{};".format(
                self.java_package,
                module_result.name,
                file.filename,
            ),
            package=self.java_package,
            body="System.out.println({});".format(action_expr),
        )
