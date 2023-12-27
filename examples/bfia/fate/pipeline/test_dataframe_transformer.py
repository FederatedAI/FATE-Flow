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

from fate_client.pipeline import FateFlowPipeline
from fate_client.pipeline.components.fate import DataFrameTransformer
from fate_client.pipeline.interface.channel import DataWarehouseChannel


def main():
    guest_party_id = "JG0100001100000010"

    pipeline = FateFlowPipeline().set_parties(guest=guest_party_id)
    transformer_0 = DataFrameTransformer(
        "transformer_0",
        namespace="test",
        name="guest",
        table=DataWarehouseChannel(
            dataset_id="upload#guest"
        )
    )
    pipeline.set_site_role("guest")
    pipeline.set_site_party_id(guest_party_id)

    pipeline.add_tasks([transformer_0])
    pipeline.protocol_kind = "bfia"
    pipeline.conf.set(
        "extra",
        dict(initiator={'party_id': 'JG0100001100000010', 'role': 'guest'})
    )
    pipeline.compile()
    # print(pipeline.get_dag())
    pipeline.fit()


if __name__ == "__main__":
    main()