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

from uberpoet import blazeprojectgen, cpprojectgen

from uberpoet.commandlineutil import Graph


def gen_ios_project(args, graph: Graph) -> dict:
    gen = project_generator_for_arg(args)

    logging.info("Project Generator type: %s", args.project_generator_type)
    logging.info("Generation type: %s", args.gen_type)
    logging.info(
        "Creating a {} module count mock app in {}".format(
            len(graph.node_list), args.output_directory
        )
    )
    logging.info(
        "Example command to generate Xcode workspace: $ {}".format(
            gen.example_command()
        )
    )

    gen.gen_app(
        graph.app_node,
        graph.node_list,
        graph.config.swift_lines_of_code,
        graph.config.objc_lines_of_code,
        graph.config.loc_json_file_path,
    )

    return {
        "generator_type": args.project_generator_type,
        "graph_config": args.gen_type,
        "options": {
            "use_wmo": bool(args.use_wmo),
            "use_dynamic_linking": bool(args.use_dynamic_linking),
            "swift_lines_of_code": args.swift_lines_of_code,
            "objc_lines_of_code": args.objc_lines_of_code,
        },
    }


def project_generator_for_arg(args):
    if args.project_generator_type == "buck" or args.project_generator_type == "bazel":
        if not args.blaze_module_path:
            raise ValueError(
                "Must supply --blaze_module_path when using the Buck or Bazel generators."
            )
        return blazeprojectgen.IosBlazeProjectGenerator(
            args.output_directory,
            args.blaze_module_path,
            use_wmo=args.use_wmo,
            flavor=args.project_generator_type,
        )
    elif args.project_generator_type == "cocoapods":
        return cpprojectgen.CocoaPodsProjectGenerator(
            args.output_directory,
            use_wmo=args.use_wmo,
            use_dynamic_linking=args.use_dynamic_linking,
            use_deterministic_uuids=args.cocoapods_use_deterministic_uuids,
            generate_multiple_pod_projects=args.cocoapods_generate_multiple_pod_projects,
        )
    else:
        raise ValueError(
            "Unknown project generator arg: " + str(args.project_generator_type)
        )
