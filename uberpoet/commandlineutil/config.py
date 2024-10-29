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

from dataclasses import dataclass
from typing import List

from .base_config import BaseAppGenerationConfig
from .ios_config import IosAppGenerationConfig
from .java_config import JavaAppGenerationConfig
from .graph import gen_graph

from uberpoet.moduletree import ModuleNode


def add_app_gen_options(parser: argparse.ArgumentParser):
    BaseAppGenerationConfig.add_app_gen_options(parser)
    subparsers = parser.add_subparsers(dest="command")
    IosAppGenerationConfig.add_app_gen_options(subparsers.add_parser("ios"))
    JavaAppGenerationConfig.add_app_gen_options(subparsers.add_parser("java"))


def validate_app_gen_options(args):
    if args.command == "ios":
        IosAppGenerationConfig.validate_app_gen_options(args)
    elif args.command == "java":
        JavaAppGenerationConfig.validate_app_gen_options(args)
    else:
        raise Exception("unknown command: %s" % args.command)


@dataclass
class Graph:
    config: BaseAppGenerationConfig
    app_node: ModuleNode
    node_list: List[ModuleNode]


def create_graph(args) -> Graph:
    if args.command == "ios":
        graph_config = IosAppGenerationConfig()
    elif args.command == "java":
        graph_config = JavaAppGenerationConfig()
    else:
        raise Exception("unknown command: %s" % args.command)

    graph_config.pull_from_args(args)

    app_node, node_list = gen_graph(args.gen_type, graph_config)
    return Graph(
        graph_config,
        app_node,
        node_list,
    )
