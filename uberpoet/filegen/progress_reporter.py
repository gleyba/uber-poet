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

from typing import Callable

from uberpoet.filegen import Language


class ProgressReporter(object):
    def __init__(
        self, langs: dict[Language, int], pclbk: Callable[[Language, int, int], None]
    ):
        self.langs = langs
        self.pclbk = pclbk

    def report_progress(self, lang: Language, lines: int):
        self.pclbk(lang, lines, self.langs[lang])
