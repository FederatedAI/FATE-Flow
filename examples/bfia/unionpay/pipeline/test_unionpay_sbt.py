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
from fate_client.pipeline.adapters.bfia.components.unionpay.hetero_secureboost import HeteroSecureBoost
from fate_client.pipeline.interface import DataWarehouseChannel


pipeline = FateFlowPipeline().set_parties(
    guest="JG0100001100000010",
    host="JG0100001100000010"
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

hetero_sbt_0 = HeteroSecureBoost(
    "hetero_secureboost_1",
    id="id",
    label="y",
    learning_rate=0.5,
    objective_param={"objective": "cross_entropy"},
    num_trees=2,
    subsample_feature_rate=1,
    n_iter_no_change=True,
    tol=0.0001,
    predict_param={"threshold": 0.5},
    cv_param={"n_splits": 5, "shuffle": False, "random_seed": 103, "need_cv": False},
    metrics=["auc", "ks"],
    early_stopping_rounds="",
    tree_param={"max_depth": 5},
    connect_engine="mesh",
    train_data=intersection_0.outputs["train_data"]
)

pipeline.add_task(intersection_0)
pipeline.add_task(hetero_sbt_0)
pipeline.conf.set(
    "extra",
    dict(initiator={'party_id': 'JG0100001100000010', 'role': 'guest'})
)

pipeline.protocol_kind = "bfia"
pipeline.guest.conf.set("resources", dict(cpu=-1, disk=-1, memory=-1))
pipeline.hosts[0].conf.set("resources", dict(cpu=-1, disk=-1, memory=-1))
pipeline.compile()
pipeline.fit()
