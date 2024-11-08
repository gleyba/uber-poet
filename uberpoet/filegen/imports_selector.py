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

import random

from abc import ABC, abstractmethod
from dataclasses import dataclass

from .filegen import *


@dataclass
class ClassKey:
    file_idx: int
    class_idx: int


@dataclass
class InnerKey:
    file_idx: int
    class_idx: int
    func_idx: int


@dataclass
class InnerImportSelector:
    def __init__(self, inners: list[FileSpec]):
        self.inners = inners
        self.key = self.InnerKey(0, 0, 0)
        self.imports_count = 0
        for file_spec in inners:
            self.imports_count += file_spec.imports_count

    def advance(self, count: int, restart: bool):
        while count > 0:
            cur_class = self.inners[self.key.file_idx].classes[self.key.class_idx]
            func_len = len(cur_class.func_keys)
            if self.key.func_idx + count >= func_len:
                count -= func_len - count
                self.key.func_idx = 0
                self.key.class_idx += 1
                if self.key.class_idx < len(self.inners[self.key.file_idx].classes):
                    continue
                self.key.class_idx = 0
                self.key.file_idx += 1
                if self.key.file_idx < len(self.inners):
                    continue
                self.key.file_idx = 0
                if not restart:
                    return count
            else:
                self.key.func_idx += count
        return 0

    def cur_key(self) -> InnerKey:
        cur_class = self.inners[self.key.file_idx].classes[self.key.class_idx]
        return self.InnerKey(
            self.key.file_idx,
            cur_class.key,
            cur_class[self.func_idx],
        )


@dataclass
class ExternalKey:
    module_name: str
    inner_key: InnerKey


@dataclass
class ExternalImportSelector:
    @dataclass
    class ExternalDef:
        name: str
        selector: InnerImportSelector

    def __init__(self, externals: list[ModuleResult]):
        self.external_idx = 0
        self.externals = [
            self.ExternalDef(
                module.name,
                InnerImportSelector([file.classes for file in module.files.values()]),
            )
            for module in externals
        ]
        self.imports_count = 0
        for external in self.externals:
            self.imports_count += external.selector.imports_count

    def advance(self, count: int):
        while count > 0:
            cur = self.externals[self.external_idx]
            count = cur.selector.advance(count, False)
            if count:
                self.external_idx += 1
            if self.external_idx < len(self.externals):
                continue
            self.external_idx = 0

    def cur_key(self) -> ExternalKey:
        cur = self.externals[self.external_idx]
        return ExternalKey(cur.name, cur.selector.cur_key())


class InnerImportsResult:
    @dataclass
    class ClassImportsResult:
        class_to_functions: dict[int, set[int]]

    def __init__(self):
        self.file_to_classes: dict[int, self.ClassImportsResult] = {}
        self.count = 0

    def add(self, key: InnerKey) -> bool:
        if not key.file_idx in self.file_to_classes:
            self.file_to_classes[key.file_idx] = self.ClassImportsResult(
                {
                    key.class_idx,
                    [key.func_idx],
                }
            )
        elif not key.class_idx in self.file_to_classes[key.file_idx].class_to_functions:
            self.file_to_classes[key.file_idx].class_to_functions[key.class_idx] = set(
                key.func_idx
            )
        elif (
            not key.func_idx
            in self.file_to_classes[key.file_idx].class_to_functions[key.class_idx]
        ):
            self.file_to_classes[key.file_idx].class_to_functions[key.class_idx].add(
                key.func_idx
            )
        else:
            return False

        self.count += 1
        return True


@dataclass
class ExternalImportsResult:
    def __init__(self):
        self.module_to_inner_imports: dict[str:InnerImportsResult] = {}
        self.count = 0

    def add(self, key: ExternalKey):
        if not key.module_name in self.module_to_inner_imports:
            self.module_to_inner_imports[key.module_name] = InnerImportsResult()

        if not self.module_to_inner_imports[key.module_name].add(key.inner_key):
            return False

        self.count += 1
        return True


class ImportsSelector(ABC):
    @abstractmethod
    def get_inner_imports(self, caller_key: ClassKey) -> InnerImportsResult:
        pass

    def get_external_imports(self) -> ExternalImportsResult:
        pass


class ImportsSelectorImpl(ImportsSelector):
    def __init__(
        self,
        inners: list[FileSpec],
        inners_imports_per_class: int,
        externals: list[ModuleResult],
        external_imports_per_class: int,
    ):
        super().__init__()
        self.inners_selector = InnerImportSelector(inners)
        self.inners_imports_per_class = min(
            inners_imports_per_class, self.inners_selector.imports_count / 2
        )
        self.inner_imports_step = max(
            1,
            int(self.inners_selector.imports_count / self.inners_imports_per_class) - 1,
        )
        self.externals_selector = ExternalImportSelector(externals)
        self.external_imports_per_class = min(
            external_imports_per_class, self.externals_selector.imports_count / 3
        )
        self.external_imports_step = max(
            1,
            int(self.externals_selector.imports_count / self.external_imports_per_class)
            - 1,
        )

    def get_inner_imports(self, caller_key: ClassKey) -> InnerImportsResult:
        result = InnerImportsResult()
        while result.count < self.inners_imports_per_class:
            self.inners_selector.advance(self.inner_imports_step, True)
            cur_key = self.inners_selector.cur_key()
            if (
                caller_key.file_idx == cur_key.file_idx
                and caller_key.class_idx == cur_key.class_idx
            ):
                continue
            result.add(cur_key)

        return result

    def get_external_imports(self) -> ExternalImportsResult:
        result = ExternalImportsResult()
        while result.count < self.external_imports_per_class:
            self.externals_selector.advance(self.external_imports_step)
            result.add(self.externals_selector.cur_key())

        return result


class ImportsSelectorDummy(ImportsSelector):
    def __init__(self, inners_imports_per_class: int, external_imports_per_class: int):
        super().__init__()
        self.inners_imports_per_class = inners_imports_per_class
        self.external_imports_per_class = external_imports_per_class

    @staticmethod
    def random_inner_key() -> InnerKey:
        return InnerKey(
            random.randint(0, 31),
            random.randint(0, 9),
            random.randint(0, 9),
        )

    @staticmethod
    def random_external_key() -> ExternalKey:
        return ExternalKey(
            "test{}".format(random.randint(0, 31)),
            ImportsSelectorDummy.random_inner_key(),
        )

    def get_inner_imports(self, caller_key: ClassKey) -> InnerImportsResult:
        result = InnerImportsResult()
        while result.count < self.inners_imports_per_class:
            cur_key = self.random_inner_key()
            if (
                caller_key.file_idx == cur_key.file_idx
                and caller_key.class_idx == cur_key.class_idx
            ):
                continue
            result.add(cur_key)

        return result

    def get_external_imports(self) -> ExternalImportsResult:
        result = ExternalImportsResult()
        while result.count < self.external_imports_per_class:
            result.add(self.random_external_key())

        return result
