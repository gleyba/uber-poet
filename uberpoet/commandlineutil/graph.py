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

import logging
from os.path import join

from typing import List, Tuple
from toposort import toposort_flatten

from uberpoet import dotreader
from uberpoet.moduletree import ModuleGenType, ModuleNode

from .base_config import BaseAppGenerationConfig


def gen_graph(
    gen_type: ModuleGenType, config: BaseAppGenerationConfig
) -> Tuple[ModuleNode, List[ModuleNode]]:
    # app_node, node_list = None, None
    modules_per_layer = config.module_count / config.app_layer_count

    if gen_type == ModuleGenType.flat:
        app_node, node_list = ModuleNode.gen_flat_graph(config.module_count)
    elif gen_type == ModuleGenType.bs_flat:
        app_node, node_list = ModuleNode.gen_flat_big_small_graph(
            config.big_module_count, config.small_module_count
        )
    elif gen_type == ModuleGenType.layered:
        app_node, node_list = ModuleNode.gen_layered_graph(
            config.app_layer_count, modules_per_layer
        )
    elif gen_type == ModuleGenType.bs_layered:
        app_node, node_list = ModuleNode.gen_layered_big_small_graph(
            config.big_module_count, config.small_module_count
        )
    elif (
        gen_type == ModuleGenType.dot
        and config.dot_file_path
        and config.dot_root_node_name
    ):
        logging.info("Reading dot file: %s", config.dot_file_path)
        app_node, parsed_node_list = dotreader.DotFileReader().read_dot_file(
            config.dot_file_path, config.dot_root_node_name
        )
        node_graph = {n: set(n.deps) for n in parsed_node_list}
        node_list = toposort_flatten(node_graph)
    else:
        logging.error("Unexpected argument set, aborting.")
        item_list = ", ".join(ModuleGenType.enum_list())
        logging.error(
            "Choose from ({}) module count: {} dot path: {} ".format(
                item_list, config.module_count, config.dot_path
            )
        )
        raise ValueError("Invalid Arguments")

    return app_node, node_list
