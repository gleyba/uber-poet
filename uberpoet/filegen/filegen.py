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

from abc import ABC
from dataclasses import dataclass

from uberpoet.util import (
    classproperty,
    first_key,
    first_in_dict,
    seed,
)

uber_poet_header = """
// This code was @generated by Uber Poet, a mock application generator.
// Check it out at https://github.com/gleyba/uber-poet
"""


class Language(object):
    def __init__(self, value):
        self.value = value

    @classproperty
    def SWIFT(_):
        return Language("Swift")

    @classproperty
    def OBJC(_):
        return Language("Objective-C")

    @classproperty
    def JAVA(_):
        return Language("Java")

    @staticmethod
    def from_str(value: str):
        if value == "Swift":
            return Language.SWIFT
        elif value == "Objective-C":
            return Language.OBJC
        elif value == "Java":
            return Language.JAVA
        else:
            raise Exception("Unknown language: %s" % value)

    @staticmethod
    def enum_list():
        return [Language.SWIFT, Language.OBJC, Language.JAVA]

    def __eq__(self, other):
        if type(other) == str:
            return self.value == other
        else:
            return self.value == other.value

    def __hash__(self):
        return hash(self.value)


@dataclass
class ClassSpec:
    key: int
    func_keys: list[int]


class FileSpec(object):
    def __init__(self, file_idx: int, class_count: int, function_count: int):
        self.file_idx = file_idx
        self.funcs = [seed() for _ in range(function_count)]
        self.classes = [
            ClassSpec(seed(), [seed() for _ in range(function_count)])
            for _ in range(class_count)
        ]
        self.imports_count = class_count * function_count


class FileResult(object):
    def __init__(self, filename: str, language: Language, text, functions, classes):
        super(FileResult, self).__init__()
        self.filename = filename
        self.language = language
        self.text = text  # string
        self.text_line_count = text.count("\n")
        self.functions = functions  # list of indexes
        self.classes = classes  # {class index: {func type: function indexes}}

    def __str__(self):
        return "<text_line_count : {} functions : {} classes : {}>".format(
            self.text_line_count,
            self.functions,
            self.classes,
        )

    def basename(self):
        return self.filename.split(".")[0]

    def first_class_and_func(self):
        if type(self.classes) == dict:
            class_key = first_key(self.classes)
            class_index = first_in_dict(self.classes)
            function_key = first_in_dict(class_index)[0]
        elif type(self.classes) == FileSpec:
            class_key = self.classes.classes[0].key
            function_key = self.classes.classes[0].func_keys[0]

        return class_key, function_key


@dataclass
class ModuleResult:
    name: str
    files: dict[str, FileResult]
    loc: int
    language: Language

    def first_file(self) -> FileResult:
        return first_in_dict(self.files)


class FileGenerator(ABC):
    pass
