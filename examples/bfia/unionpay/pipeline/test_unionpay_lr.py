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
from fate_client.pipeline.adapters.bfia.components.unionpay.intersection import Intersection
from fate_client.pipeline.adapters.bfia.components.unionpay.hetero_lr import HeteroLR
from fate_client.pipeline.interface import DataWarehouseChannel


pipeline = FateFlowPipeline().set_parties(
    guest="JG0100001100000010",
    host="JG0100001100000010",
    arbiter="JG0100001100000010"
)
pipeline.set_site_role("guest")
pipeline.set_site_party_id("JG0100001100000010")

intersection_0 = Intersection(
    "intersect_rsa_1",
    id="id",
    intersect_method="rsa",
    only_output_key=False,
    rsa_params=dict(
        final_hash_method="sha256",
        hash_method="sha256",
        key_length=2048
    ),
    sync_intersect_ids=True,
    connect_engine="mesh",
    train_data=[
        DataWarehouseChannel(dataset_id="testspace#test_guest", parties=dict(guest="JG0100001100000010")),
        DataWarehouseChannel(dataset_id="testspace#test_host", parties=dict(host="JG0100001100000010"))
    ]
)

hetero_lr_0 = HeteroLR(
    "hetero_logistic_regression_1",
    id="id",
    label="y",
    batch_size=-1,
    penalty="L2",
    early_stop="diff",
    tol=0.0001,
    max_iter=2,
    alpha=0.01,
    optimizer="nesterov_momentum_sgd",
    init_param={"init_method":"zeros"},
    learning_rate=0.15,
    connect_engine="mesh",
    train_data=intersection_0.outputs["train_data"]
)

pipeline.add_task(intersection_0)
pipeline.add_task(hetero_lr_0)
pipeline.conf.set(
    "extra",
    dict(initiator={'party_id': 'JG0100001100000010', 'role': 'guest'})
)

pipeline.protocol_kind = "bfia"
pipeline.guest.conf.set("resources", dict(cpu=-1, disk=-1, memory=-1))
pipeline.hosts[0].conf.set("resources", dict(cpu=-1, disk=-1, memory=-1))
pipeline.compile()
pipeline.fit()
