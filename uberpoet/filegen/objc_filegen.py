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

from uberpoet.util import seed

from .filegen import *
from .swift_filegen import FuncType, get_import_func_calls

objc_header_func_template = (
    """- (int)complexCrap{0}:(int)arg stuff:(nonnull NSString *)stuff;"""
)

objc_source_func_template = """
- (int)complexCrap{0}:(int)arg stuff:(nonnull NSString *)stuff;
{{
    int a = (int)(4 * self.{1} + (int)((float)arg / 32.0));
    int b = (int)(4 * self.{1} + (int)((float)arg / 32.0));
    int c = (int)(4 * self.{1} + (int)((float)arg / 32.0));
    return (int)(4 * self.{1} + (int)((float)arg / 32.0)) + a + b + c;
}}"""

objc_system_import_template = """
@import Foundation;
"""

objc_header_template = """
@interface MyClass_{0} : NSObject

@property(nonatomic, readonly) int x;
@property(nonatomic, readonly, nonnull) NSString *y;

- (nonnull instancetype)initWithX:(int)x y:(nonnull NSString *)y;
{1}

@end
"""

objc_source_template = """
@implementation MyClass_{0}

- (nonnull instancetype)initWithX:(int)x y:(nonnull NSString *)y;
{{
    self = [super init];
    NSParameterAssert(self);

    _x = x;
    _y = y;
    {2}
    return self;
}}
{1}

@end
"""


class ObjCHeaderFileGenerator(FileGenerator):
    @staticmethod
    def language():
        return Language.OBJC

    @staticmethod
    def extension():
        return ".h"

    @staticmethod
    def gen_func(nums):
        out = []

        for num in nums:
            out.append(objc_header_func_template.format(num))

        return "\n".join(out), nums

    def get_header(self, objc_class):
        out = []
        class_nums = {}

        for c in objc_class.classes:
            num = c
            func_out, func_nums = self.gen_func(
                objc_class.classes[c][FuncType.OBJC_FRIENDLY]
            )
            out.append(objc_header_template.format(num, func_out))
            class_nums[num] = {FuncType.OBJC_FRIENDLY: func_nums}

        return "\n".join(out), class_nums

    def gen_file(self, objc_class):
        class_out, class_nums = self.get_header(objc_class)

        chunks = [uber_poet_header, objc_system_import_template, class_out]

        return FileResult("\n".join(chunks), [], class_nums, Language.OBJC)


class ObjCSourceFileGenerator(FileGenerator):
    @staticmethod
    def language():
        return Language.OBJC

    @staticmethod
    def extension():
        return ".m"

    @staticmethod
    def gen_func(function_count, var_name):
        out = []
        nums = []

        for _ in range(function_count):
            num = seed()
            text = objc_source_func_template.format(num, var_name)
            nums.append(num)
            out.append(text)

        return "\n".join(out), nums

    def gen_class(self, class_count, func_per_class_count, import_list):
        out = []
        class_nums = {}

        for _ in range(class_count):
            num = seed()
            func_out, func_nums = self.gen_func(func_per_class_count, "x")
            func_call_out = get_import_func_calls(
                self.language(), import_list, indent=4
            )
            out.append(objc_source_template.format(num, func_out, func_call_out))
            class_nums[num] = {FuncType.OBJC_FRIENDLY: func_nums}

        return "\n".join(out), class_nums

    def gen_file(self, class_count, function_count, import_list=None):
        if import_list is None:
            import_list = []
        imports = []
        for i in import_list:
            if type(i) is str:
                imports.append('#import "{}"'.format(i))
            elif type(i) is dict:
                imports.append("@import {};".format(i.keys()[0]))
        imports_out = "\n".join(imports)
        class_out, class_nums = self.gen_class(class_count, 5, import_list)

        chunks = [uber_poet_header, objc_system_import_template, imports_out, class_out]

        return FileResult("\n".join(chunks), [], class_nums, Language.OBJC)
