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
import logging

from fate_flow.components import LOCAL, Output, DatasetArtifact, cpn


@cpn.component(roles=[LOCAL])
@cpn.parameter("path", type=str, default=None, optional=False)
@cpn.parameter("format", type=str, default="csv", optional=False)
@cpn.parameter("id_name", type=str, default="id", optional=True)
@cpn.parameter("delimiter", type=str, default=",", optional=True)
@cpn.parameter("label_name", type=str, default=None, optional=True)
@cpn.parameter("label_type", type=str, default="float32", optional=True)
@cpn.parameter("dtype", type=str, default="float32", optional=True)
@cpn.artifact("output_data", type=Output[DatasetArtifact], roles=[LOCAL])
def upload(
    path, format, id_name, delimiter, label_name, label_type, dtype, output_data
):
    output_data.uri = "test"
    upload_data(path, id_name, delimiter, label_name, label_type, dtype, output_data)


def upload_data(*args):
    pass
