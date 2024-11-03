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
import json
import logging
import sys
import time
import os
import shutil
from os.path import join
from typing import Callable

from uberpoet.commandlineutil import (
    validate_app_gen_options,
    add_app_gen_options,
    create_graph,
    Graph,
)
from uberpoet.filegen import Language

from .genproj_ios import gen_ios_project
from .genproj_java import gen_java_project


class GenProjCommandLine(object):
    @staticmethod
    def make_args(args):
        """Parses command line arguments"""
        arg_desc = "Generate a fake test project with many modules"

        parser = argparse.ArgumentParser(description=arg_desc)
        add_app_gen_options(parser)
        args = parser.parse_args(args)
        validate_app_gen_options(args)
        return args

    @staticmethod
    def create_progress_fn():
        def get_current_time_milli():
            return int(round(time.time() * 1000))

        last_millis = get_current_time_milli()
        throttle_time_limit = 500
        accumulate_lines_count = 0
        accumulate_lines_count_total = 0

        def progress_clbk(lang: Language, lines: int, total: int):
            nonlocal last_millis
            nonlocal throttle_time_limit
            nonlocal accumulate_lines_count
            nonlocal accumulate_lines_count_total
            curr_millis = get_current_time_milli()

            accumulate_lines_count += lines
            accumulate_lines_count_total += lines
            if (curr_millis - last_millis) < throttle_time_limit:
                return

            print(
                "%s generated lines since last check: %s, total: %s"
                % (lang.value, accumulate_lines_count, accumulate_lines_count_total)
            )
            last_millis = curr_millis
            accumulate_lines_count = 0

        return progress_clbk

    def main(self, args=None):
        if args is None:
            args = sys.argv[1:]

        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s %(levelname)s %(funcName)s: %(message)s",
        )
        start = time.time()

        args = self.make_args(args)
        graph = create_graph(args)

        if args.print_dependency_graph:
            print_nodes(graph)
            exit(0)

        logging.info("Starting Project Generation for: %s", args.command)

        del_old_output_dir(args.output_directory)

        project_info = gen_project(
            args,
            graph,
            GenProjCommandLine.create_progress_fn(),
        )

        fin = time.time()
        logging.info("Done in %f s", fin - start)

        project_info["time_to_generate"] = fin - start

        with open(
            join(args.output_directory, "project_info.json"), "w"
        ) as project_info_json_file:
            json.dump(project_info, project_info_json_file)


def gen_project(
    args, graph: Graph, pclbk: Callable[[Language, int, int], None]
) -> dict:
    if args.command == "ios":
        return gen_ios_project(args, graph, pclbk)
    elif args.command == "java":
        return gen_java_project(args, graph, pclbk)


def print_nodes(graph: Graph):
    edges = [(node.name, dep.name) for node in graph.node_list for dep in node.deps]
    for edge in edges:
        print(edge[0], edge[1])


def del_old_output_dir(output_directory):
    if os.path.isdir(output_directory):
        logging.warning("Deleting old mock app directory %s", output_directory)
        shutil.rmtree(output_directory)


def main():
    GenProjCommandLine().main()


if __name__ == "__main__":
    main()
