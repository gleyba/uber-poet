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

from uberpoet.filegen.imports_selector import *

import unittest


class TestImportsSelector(unittest.TestCase):
    def test_import_selector(self):
        imports_selector = ImportsSelectorImpl(
            inners=[
                FileSpec.new_with_seed(
                    file_idx=file_idx,
                    class_count=3,
                    function_count=3,
                )
                for file_idx in range(8)
            ],
            inners_imports_per_class=4,
            externals=[
                ModuleResult(
                    name="name{}".format(module_idx),
                    files={
                        "File{}.java".format(i): FileResult(
                            filename="File{}.java".format(i),
                            language=Language.JAVA,
                            text="",
                            spec=FileSpec.new_with_seed(i, 3, 3),
                        )
                        for i in range(10)
                    },
                    loc=1000,
                    language=Language.JAVA,
                )
                for module_idx in range(10)
            ],
            external_imports_per_class=16,
        )
        inner_imports = imports_selector.get_inner_imports(ClassKey(0, 0))
        assert inner_imports.count == 4
        external_imports = imports_selector.get_external_imports()
        assert external_imports.count == 16


if __name__ == "__main__":
    unittest.main()
