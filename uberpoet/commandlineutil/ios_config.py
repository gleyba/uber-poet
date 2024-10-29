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

import argparse
import logging

from .base_config import BaseAppGenerationConfig

from uberpoet.moduletree import ModuleGenType
from uberpoet.util import bool_xor


class IosAppGenerationConfig(BaseAppGenerationConfig):
    def __init__(
        self,
        module_count=0,
        big_module_count=0,
        small_module_count=0,
        swift_lines_of_code=0,
        objc_lines_of_code=0,
        app_layer_count=0,
        dot_file_path="",
        dot_root_node_name="",
        loc_json_file_path="",
    ):
        self.module_count = module_count
        self.big_module_count = big_module_count
        self.small_module_count = small_module_count
        self.swift_lines_of_code = swift_lines_of_code
        self.objc_lines_of_code = objc_lines_of_code
        self.app_layer_count = app_layer_count
        self.dot_file_path = dot_file_path
        self.dot_root_node_name = dot_root_node_name
        self.loc_json_file_path = loc_json_file_path

    def pull_from_args(self, args):
        self.validate_app_gen_options(args)
        BaseAppGenerationConfig.pull_from_args(self, args)
        self.swift_lines_of_code = args.swift_lines_of_code
        self.objc_lines_of_code = args.objc_lines_of_code
        self.loc_json_file_path = args.loc_json_file_path

    @staticmethod
    def add_app_gen_options(parser: argparse.ArgumentParser):
        parser.add_argument(
            "-pgt",
            "--project_generator_type",
            choices=["buck", "bazel", "cocoapods"],
            default="buck",
            required=False,
            help="The project generator type to use.  Supported types are Buck, Bazel and CocoaPods. Default is `buck`",
        )
        parser.add_argument(
            "-bmp",
            "--blaze_module_path",
            help="The root of the Buck or Bazel dependency path of the generated code.  Only used if Buck or Bazel "
            "generator type is used.",
        )
        parser.add_argument(
            "-wmo",
            "--use_wmo",
            default=False,
            help="Whether or not to use whole module optimization when building swift modules.",
        )
        parser.add_argument(
            "-udl",
            "--use_dynamic_linking",
            default=False,
            help="Whether or not to generate a project in which the modules are dynamically linked.  By default all "
            "projects use static linking. This option is currently used only by the CocoaPods generator.",
        )

        ios = parser.add_argument_group("Ios app generation options")
        (
            ios.add_argument(
                "--swift_lines_of_code",
                default=1500000,  # 1.5 million lines of code
                type=int,
                help="Approximately how many lines of Swift code each mock app should have.",
            ),
        )
        (
            ios.add_argument(
                "--objc_lines_of_code",
                default=0,
                type=int,
                help="Approximately how many lines of ObjC code each mock app should have.",
            ),
        )

        parser.add_argument(
            "--loc_json_file_path",
            default="",
            type=str,
            help="A JSON file used to provide module LOC data.  Only used when dot graph type is used to create "
            "modules with proportional LOC.  You may generate this file using `cloc` or another tool like `tokei`."
            "  The format of the file is expected to contain each module name as a key with a value denoting the LOC.",
        )

        # CocoaPods specific options
        cocoa = parser.add_argument_group("Cocoapods mock app config")
        cocoa.add_argument(
            "--cocoapods_use_deterministic_uuids",
            default=True,
            help="Whether to use deterministic uuids within the CocoaPods generated project.  Defaults to `true`.",
        )
        cocoa.add_argument(
            "--cocoapods_generate_multiple_pod_projects",
            default=False,
            help="Whether to generate multiple pods projects.  Defaults to `false`.",
        )

    @staticmethod
    def validate_app_gen_options(args):
        BaseAppGenerationConfig.validate_app_gen_options(args)
        if bool_xor(args.dot_file_path, args.dot_root_node_name):
            logging.info(
                'dot_file_path: "%s" dot_root_node_name: "%s"',
                args.dot_file_path,
                args.dot_root_node_name,
            )
            raise ValueError(
                "If you specify a dot file config option, you must also specify a root node name using "
                '"dot_root_node_name".'
            )
        if args.loc_json_file_path and args.gen_type != ModuleGenType.dot:
            logging.info('loc_json_file_path: "%s"', args.loc_json_file_path)
            raise ValueError(
                'If you specify "loc_json_file_path", you must also specify a dot graph style.'
            )
