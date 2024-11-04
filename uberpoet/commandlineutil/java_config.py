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

import argparse

from .base_config import BaseAppGenerationConfig


class JavaAppGenerationConfig(BaseAppGenerationConfig):
    def __init__(self):
        pass

    def pull_from_args(self, args):
        self.validate_app_gen_options(args)
        BaseAppGenerationConfig.pull_from_args(self, args)
        self.java_lines_of_code = args.java_lines_of_code
        self.java_package = args.java_package

    @staticmethod
    def add_app_gen_options(parser: argparse.ArgumentParser):
        java = parser.add_argument_group("Ios app generation options")
        (
            java.add_argument(
                "--java_lines_of_code",
                default=1500000,  # 1.5 million lines of code
                type=int,
                help="Approximately how many lines of Java code each mock app should have.",
            ),
            java.add_argument(
                "--java_package",
                default="com.example",
                type=str,
                help="Base Java package to use in generated files.",
            ),
        )

    @staticmethod
    def validate_app_gen_options(args):
        BaseAppGenerationConfig.validate_app_gen_options(args)
