#  Copyright (c) 2021 Uber Technologies, Inc.
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

import json
import logging
import tempfile
import subprocess

from math import ceil
from os.path import join

from .filegen import Language
from .filegen import Language
from .memoize import memoized


class LOCCalculator(object):
    @memoized
    def calculate_loc(self, text, language):
        # actual code = lines of code, minus whitespace
        # calculated using cloc
        if language == Language.SWIFT:
            extension = ".swift"
        elif language == Language.OBJC:
            extension = ".m"
        else:
            raise ValueError("Unknown language: {}".format(language))

        tmp_file_path = join(
            tempfile.gettempdir(), "ub_mock_gen_example_file{}".format(extension)
        )
        with open(tmp_file_path, "w") as f:
            f.write(text)
        loc = count_loc(tmp_file_path, language)

        if loc == -1:
            logging.warning(
                "Using fallback loc calc method due to cloc not being installed."
            )
            if language == Language.SWIFT:
                # fallback if cloc is not installed
                # this fallback is based on running cloc on the file made by `self.swift_gen.gen_file(3, 3)`
                # and saving the result of cloc(file_result.text) / file_result.text_line_count to here:
                fallback_code_multiplier = 0.811537333
            elif language == Language.OBJC:
                # fallback if cloc is not installed
                # this fallback is based on running cloc on the file made by `self.objc_source_gen.gen_file(3, 3)`
                # and saving the result of cloc(file_result.text) / file_result.text_line_count to here:
                fallback_code_multiplier = 0.772727272
            else:
                raise ValueError(
                    "No fallback multiplier calculated for language: {}".format(
                        language
                    )
                )

            loc = int(ceil(len(text.split("\n")) * fallback_code_multiplier))

        return loc


def count_loc(code_path, language=Language.SWIFT):
    """Returns the number of lines of code in `code_path` using cloc. If cloc is not
    on your system or there is an error, then it returns -1"""
    try:
        logging.info("Counting lines of code in %s", code_path)
        raw_json_out = subprocess.check_output(["cloc", "--quiet", "--json", code_path])
    except OSError:
        logging.warning("You do not have cloc installed, skipping line counting.")
        return -1

    json_out = json.loads(raw_json_out)
    language_loc = json_out.get(language, {}).get("code", 0)
    if not language_loc:
        logging.error('Unexpected cloc output "%s"', raw_json_out)
        raise ValueError("cloc did not give a correct value")
    return language_loc
