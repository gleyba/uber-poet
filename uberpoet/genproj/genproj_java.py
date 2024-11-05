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

import logging

from typing import Callable

from uberpoet.filegen import Language
from uberpoet.commandlineutil import Graph
from uberpoet.filegen import ProgressReporter
from uberpoet.commandlineutil import JavaAppGenerationConfig
from uberpoet.blazeprojectgen import JavaBlazeProjectGenerator


def gen_java_project(
    config: JavaAppGenerationConfig,
    graph: Graph,
    pclbk: Callable[[Language, int, int], None],
) -> dict:
    reporter = ProgressReporter(
        {Language.JAVA: config.java_lines_of_code},
        pclbk,
    )
    gen = JavaBlazeProjectGenerator(config, reporter)

    logging.info(
        "Creating a {} module count mock app in {}".format(
            len(graph.node_list),
            config.output_directory,
        )
    )

    gen.gen_app(
        graph.app_node,
        graph.node_list,
        {Language.JAVA: config.java_lines_of_code},
    )

    return {
        "graph_config": config.gen_type,
        "options": {
            "java_lines_of_code": config.java_lines_of_code,
        },
    }
