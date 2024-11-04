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

from .filegen import *

func_call_template = """{0}.MyClass{1}.complexCrap{2}(4, 2)"""


class JavaFileGenerator(FileGenerator):
    def __init__(self, main_template: str, java_package: str):
        super().__init__()
        self.main_template = main_template
        self.java_package = java_package

    def gen_main(self, module_result: ModuleResult):
        file = module_result.first_file()
        class_num, func_num = file.first_class_and_func()
        action_expr = func_call_template.format(
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
            body="System.out.println({});".format(action_expr),
        )
