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

class Pipelined:

    def __init__(self, *, role=None, party_id=None, model_id=None, party_model_id=None, model_version):
        if party_model_id is None:
            self.role = role
            self.party_id = party_id
            self.model_id = model_id
            self.party_model_id = f'{role}#{party_id}#{model_id}'
        else:
            self.role, self.party_id, self.model_id = party_model_id.split('#', 2)
            self.party_model_id = party_model_id

        self.model_version = model_version
