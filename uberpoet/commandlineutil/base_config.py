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

import os
import argparse

from uberpoet.moduletree import ModuleGenType


class BaseAppGenerationConfig(object):
    def pull_from_args(self, args):
        self.concurrency = args.concurrency
        self.module_count = args.module_count
        self.big_module_count = args.big_module_count
        self.small_module_count = args.small_module_count
        self.app_layer_count = args.app_layer_count
        self.dot_file_path = args.dot_file_path
        self.dot_root_node_name = args.dot_root_node_name

    @staticmethod
    def add_app_gen_options(parser: argparse.ArgumentParser):
        parser.add_argument(
            "-o",
            "--output_directory",
            required=True,
            help="Where the mock project should be output.",
        )
        parser.add_argument(
            "--print_dependency_graph",
            default=False,
            help="If true, prints out the dependency edge list and exits instead of generating an application.",
        )
        parser.add_argument(
            "-gt",
            "--gen_type",
            required=True,
            choices=ModuleGenType.enum_list(),
            help="What kind of mock app generation you want.  See layer_types.md for a description of graph types.",
        )
        parser.add_argument(
            "--concurrency",
            default=os.cpu_count(),
            type=int,
            help="Concurrent workers amount to generate modules",
        )

        app = parser.add_argument_group("Mock app generation options")
        (
            app.add_argument(
                "--module_count",
                default=100,
                type=int,
                help="How many modules should be in a normal mock app type.",
            ),
        )

        app.add_argument(
            "--app_layer_count",
            default=10,
            type=int,
            help="How many module layers there should be in the layered mock app type.",
        )

        (
            app.add_argument(
                "--big_module_count",
                default=3,
                type=int,
                help="How many big modules should be in a big/small mock app type.",
            ),
        )
        (
            app.add_argument(
                "--small_module_count",
                default=50,
                type=int,
                help="How many small modules should be in a big/small mock app type.",
            ),
        )

        dot = parser.add_argument_group("Dot file mock app config")
        dot.add_argument(
            "--dot_file_path",
            default="",
            type=str,
            help="The path to the dot file to create a mock module graph from.  This dot file for Buck can be "
            'created like so: `buck query "deps(target)" --dot > file.gv`.  Alternatively, you may use your own'
            "means to generate it for different project types.",
        )
        dot.add_argument(
            "--dot_root_node_name",
            default="",
            type=str,
            help="The name of the root application node of the dot file, such as 'App'.",
        )

    @staticmethod
    def validate_app_gen_options(args):
        pass
