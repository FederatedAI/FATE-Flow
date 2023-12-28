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

import argparse

from fate_client.pipeline import FateFlowPipeline
from fate_client.pipeline.components.fate import HeteroSecureBoost, PSI, Reader
from fate_client.pipeline.components.fate import Evaluation
from fate_client.pipeline.interface.channel import DataWarehouseChannel


def main():
    guest = "JG0100001100000010"
    host = "JG0100001100000010"

    pipeline = FateFlowPipeline().set_parties(guest=guest, host=host)

    pipeline.set_site_role("guest")
    pipeline.set_site_party_id(guest)

    psi_0 = PSI("psi_0",
                input_data=[DataWarehouseChannel(dataset_id="experiment#breast_hetero_guest", parties=dict(guest=guest)),
                            DataWarehouseChannel(dataset_id="experiment#breast_hetero_host", parties=dict(host=host))])
    hetero_sbt_0 = HeteroSecureBoost(
        "hetero_sbt_0",
        train_data=psi_0.outputs["output_data"],
        num_trees=1,
        max_depth=3,
    )


    pipeline.add_tasks([psi_0, hetero_sbt_0])

    pipeline.protocol_kind = "bfia"
    pipeline.conf.set(
        "extra",
        dict(initiator={'party_id': guest, 'role': 'guest'})
    )
    pipeline.guest.conf.set("resources", dict(cpu=-1, disk=-1, memory=-1))
    pipeline.hosts[0].conf.set("resources", dict(cpu=-1, disk=-1, memory=-1))
    pipeline.compile()
    pipeline.fit()


if __name__ == "__main__":
    main()