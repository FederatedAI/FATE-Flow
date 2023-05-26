#
#  Copyright 2019 The FATE Authors. All Rights Reserved.
#
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.
#
import argparse

from fate_flow.controller.engine_adapt import build_engine
from fate_flow.operation.job_saver import JobSaver


FUNC = ["query_status", "download_log", "download_model"]


def call_fun(func, args):
    job_id = args.job_id
    role = args.role
    party_id = args.party_id
    component_name = args.component_name
    output_path = args.output_path
    engine, task = load_engine(job_id, role, party_id, component_name)
    if func == "query_status":
        query_status(engine, task)
    elif func == "download_log":
        download_log(engine, task, output_path)

    elif func == "download_model":
        download_model(engine, task, output_path)


def load_engine(job_id, role, party_id, component_name):
    tasks = JobSaver.query_task(job_id=job_id, role=role, party_id=party_id, component_name=component_name, run_on_this_party=True)
    if tasks:
        task = tasks[0]
        if task.f_is_deepspeed:
            deepspeed_engine = build_engine(task.f_engine_conf.get("computing_engine"), task.f_is_deepspeed)
            return deepspeed_engine, task
        else:
            raise Exception(f"Not is a deepspeed task: job_id[{job_id}], role[{role}], party_id[{party_id}], component_name[{component_name}]")
    else:
        raise Exception(f"no found task: job_id[{job_id}], role[{role}], party_id[{party_id}], component_name[{component_name}]")


def query_status(engine, task):
    status = engine._query_status(task)
    print(status)


def download_log(engine, task, output_path):
    engine.download_log(task, path=output_path)
    print(output_path)


def download_model(engine, task, output_path):
    engine.download_model(task, path=output_path)
    print(output_path)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('-f', '--function', type=str,
                        choices=FUNC,
                        required=True,
                        help="function to call")
    parser.add_argument('-j', '--job_id', required=True, type=str, help="job id")
    parser.add_argument('-r', '--role', required=True, type=str, help="role")
    parser.add_argument('-p', '--party_id', required=True, type=str, help="party id")
    parser.add_argument('-cpn', '--component_name', required=True, type=str, help="component name")
    parser.add_argument('-o', '--output_path', required=False, type=str, help="output_path")
    args = parser.parse_args()
    config_data = {}
    config_data.update(dict((k, v) for k, v in vars(args).items() if v is not None))

    call_fun(args.function, args)
