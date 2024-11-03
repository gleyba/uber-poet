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

from uberpoet.util import first_in_dict, seed

from .filegen import *

# This method can only be invoked between Swift modules as it is not
# ObjC friendly due to the use of generics.
swift_func_template = """
public func complexCrap{0}<T>(arg: Int, stuff:T) -> Int {{
    let a = Int(4 * {1} + Int(Float(arg) / 32.0))
    let b = Int(4 * {1} + Int(Float(arg) / 32.0))
    let c = Int(4 * {1} + Int(Float(arg) / 32.0))
    return Int(4 * {1} + Int(Float(arg) / 32.0)) + a + b + c
}}"""


swift_func_objc_friendly_template = """
@objc
public func complexStuff{0}(arg: String) -> String {{
    let randomString = NSUUID().uuidString
    return ("\\(arg)-\\(randomString)")
}}
"""

swift_class_template = """
@objc
public class MyClass{0}: NSObject {{
    public let x: Int
    public let y: String

    @objc
    public override init() {{
        x = 7
        y = "hi"
        {2}
    }}

    {1}
}}"""

swift_to_swift_func_call_template = """MyClass{0}().complexCrap{1}(arg: 4, stuff: 2)"""
swift_to_objc_func_call_template = """MyClass_{0}().complexCrap{1}(4, stuff: \"2\")"""

objc_to_swift_func_call_template = (
    """[[[MyClass{} alloc] init] complexStuff{}WithArg:@\"4\"];"""
)
objc_to_objc_func_call_template = (
    """[[[MyClass_{} alloc] init] complexCrap{}:4 stuff:@\"2\"];"""
)

swift_to_swift_objc_friendly_func_call_template = (
    """MyClass{0}().complexStuff{1}(arg: \"4\")"""
)
swift_to_objc_friendly_func_call_template = (
    """MyClass_{0}().complexStuff{1}(arg: \"4\")"""
)


def get_func_call_template(from_language, to_language, function_type):
    if function_type == FuncType.SWIFT_ONLY:
        if from_language == Language.OBJC:
            raise ValueError("Cannot invoke SWIFT_ONLY method from ObjC!")
        return (
            swift_to_swift_func_call_template
            if to_language == Language.SWIFT
            else swift_to_objc_func_call_template
        )
    elif function_type == FuncType.OBJC_FRIENDLY:
        if from_language == Language.SWIFT:
            if to_language == Language.SWIFT:
                return swift_to_swift_objc_friendly_func_call_template
            elif to_language == Language.OBJC:
                return swift_to_objc_friendly_func_call_template
        elif from_language == Language.OBJC:
            if to_language == Language.SWIFT:
                return objc_to_swift_func_call_template
            elif to_language == Language.OBJC:
                return objc_to_objc_func_call_template


def get_import_func_calls(from_language, import_list, indent=0):
    out = []
    for i in import_list:
        if type(i) is str:
            continue
        module = first_in_dict(i)
        to_language = module["language"]
        for file_result in module["files"].values():
            for class_num, class_funcs in file_result.classes.items():
                for func_type, func_nums in class_funcs.items():
                    for func_num in func_nums:
                        if (
                            func_type == FuncType.SWIFT_ONLY
                            and from_language == Language.OBJC
                            and to_language == Language.SWIFT
                        ):
                            # We cannot invoke Swift only functions from ObjC since they use generics.
                            continue
                        text = get_func_call_template(
                            from_language, to_language, func_type
                        ).format(class_num, func_num)
                        indented_text = "\n".join(
                            " " * indent + line for line in text.splitlines()
                        )
                        out.append(indented_text)

    return "\n".join(out)


class FuncType(object):
    """
    Describes the type of function added to a class. Helps distinguish how to invoke a function
    between modules.
    """

    SWIFT_ONLY = "swift_only"
    OBJC_FRIENDLY = "objc_friendly"


class SwiftFileGenerator(FileGenerator):
    def __init__(self):
        self.gen_state = {}

    @staticmethod
    def language():
        return Language.SWIFT

    @staticmethod
    def extension():
        return ".swift"

    @staticmethod
    def gen_func(function_count, var_name, indent=0):
        out = []
        nums = []

        for _ in range(function_count):
            num = seed()
            text = swift_func_template.format(num, var_name)
            indented_text = "\n".join(" " * indent + line for line in text.splitlines())
            nums.append(num)
            out.append(indented_text)

        return "\n".join(out), nums

    @staticmethod
    def gen_objc_friendly_func(indent=0):
        out = []
        nums = []

        num = seed()
        text = swift_func_objc_friendly_template.format(num)
        indented_text = "\n".join(" " * indent + line for line in text.splitlines())
        nums.append(num)
        out.append(indented_text)

        return "\n".join(out), nums

    def gen_class(self, class_count, func_per_class_count, import_list):
        out = []
        class_nums = {}

        for _ in range(class_count):
            num = seed()
            swift_only_func_out, swift_only_func_nums = self.gen_func(
                func_per_class_count, "x", indent=4
            )
            swift_objc_friendly_func_out, swift_objc_friendly_func_nums = (
                self.gen_objc_friendly_func(indent=4)
            )
            func_out = swift_only_func_out + "\n" + swift_objc_friendly_func_out
            func_call_out = get_import_func_calls(
                self.language(), import_list, indent=8
            )
            out.append(swift_class_template.format(num, func_out, func_call_out))

            class_nums[num] = {
                FuncType.SWIFT_ONLY: swift_only_func_nums,
                FuncType.OBJC_FRIENDLY: swift_objc_friendly_func_nums,
            }

        return "\n".join(out), class_nums

    def gen_file(
        self,
        filename: str,
        class_count: int,
        function_count: int,
        import_list: list[ModuleResult],
    ):
        if import_list is None:
            import_list = []
        imports_out = "\n".join(
            ["import {}".format(i if type(i) is str else i.name) for i in import_list]
        )
        func_out, func_nums = self.gen_func(function_count, "7")
        class_out, class_nums = self.gen_class(class_count, 5, import_list)

        chunks = [uber_poet_header, imports_out, func_out, class_out]

        return FileResult(
            filename,
            Language.SWIFT,
            "\n".join(chunks),
            func_nums,
            class_nums,
        )

    def gen_main(
        self, template, importing_module_name, class_num, func_num, to_language
    ):
        import_line = "import {}".format(importing_module_name)
        action_expr = get_func_call_template(
            Language.SWIFT, to_language, FuncType.SWIFT_ONLY
        ).format(class_num, func_num)
        print_line = 'print("\\({})")'.format(action_expr)
        return template.format(
            uber_poet_header, import_line, print_line, Language.SWIFT
        )
