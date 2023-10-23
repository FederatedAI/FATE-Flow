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
from fate_flow.manager.outputs.model.handel._base import IOHandle
from fate_flow.manager.outputs.model.handel._file import FileHandle
from fate_flow.manager.outputs.model.handel._mysql import MysqlHandel
from fate_flow.manager.outputs.model.handel._tencent_cos import TencentCosHandel

__all__ = ["IOHandle", "FileHandle", "MysqlHandel", "TencentCosHandel"]
