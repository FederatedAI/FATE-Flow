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
from fate_flow.manager.components.upload import Upload, UploadParam


@cpn.component(roles=[LOCAL])
@cpn.parameter("path", type=str, default=None, optional=False)
@cpn.parameter("namespace", type=str, default=None, optional=False)
@cpn.parameter("name", type=str, default=None, optional=False)
@cpn.parameter("head", type=bool, default=True, optional=True)
@cpn.parameter("delimiter", type=str, default=",", optional=True)
@cpn.parameter("destroy", type=bool, default=False, optional=True)
@cpn.parameter("partitions", type=int, default=10, optional=True)
@cpn.parameter("extend_sid", type=bool, default=False, optional=True)
@cpn.parameter("meta", type=dict, default={}, optional=True)
@cpn.artifact("output_data", type=Output[DatasetArtifact], roles=[LOCAL])
def upload(
    job_id, path, namespace, name, head, delimiter, destroy, partitions, extend_sid, meta, output_data
):
    upload_data(job_id, path, namespace, name, head, delimiter, destroy, partitions, extend_sid, meta, output_data)


def upload_data(job_id, path, namespace, name, head, delimiter, destroy, partitions, extend_sid, meta, output_data):
    upload_object = Upload()
    data = upload_object.run(
        parameters=UploadParam(
            file=path,
            head=head,
            partitions=partitions,
            namespace=namespace,
            name=name,
            meta=meta,
            destroy=destroy,
            extend_sid=extend_sid,
            delimiter=delimiter
        ),
        job_id=job_id
    )
