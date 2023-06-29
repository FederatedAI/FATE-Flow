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
from fate_flow.components import LOCAL, Output, DatasetArtifact, cpn
from fate_flow.manager.components.download import Download, DownloadParam


@cpn.component(roles=[LOCAL])
@cpn.parameter("dir_name", type=str, default=None, optional=False)
@cpn.parameter("namespace", type=str, default=None, optional=False)
@cpn.parameter("name", type=str, default=None, optional=False)
@cpn.artifact("output_data", type=Output[DatasetArtifact], roles=[LOCAL])
def download(
        job_id, dir_name, namespace, name,  output_data
):
    download_data(job_id, dir_name, namespace, name,  output_data)


def download_data(job_id, dir_name, namespace, name,  output_data):
    download_object = Download()
    data = download_object.run(
        parameters=DownloadParam(
            namespace=namespace,
            name=name,
            dir_name=dir_name
        ),
        job_id=job_id
    )
