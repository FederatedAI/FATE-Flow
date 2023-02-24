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
from fate_flow.engine.relation_ship import Relationship
from fate_flow.entity.types import EngineType, FederationEngine, StorageEngine, ComputingEngine, FederatedMode
from fate_flow.utils import conf_utils


def get_engine_class_members(engine_class) -> list:
    members = []
    for k, v in engine_class.__dict__.items():
        if k in ["__module__", "__dict__", "__weakref__", "__doc__"]:
            continue
        members.append(v)
    return members


def get_engines():
    engines = {
        EngineType.COMPUTING: None,
        EngineType.FEDERATION: None,
        EngineType.STORAGE: None,
    }

    # check service_conf.yaml
    if (
            conf_utils.get_base_config("default_engines", {}).get(EngineType.COMPUTING)
            is None
    ):
        raise RuntimeError(f"must set default_engines on conf/service_conf.yaml")
    default_engines = conf_utils.get_base_config("default_engines")

    # computing engine
    if default_engines.get(EngineType.COMPUTING) is None:
        raise RuntimeError(
            f"{EngineType.COMPUTING} is None,"
            f"Please check default_engines on conf/service_conf.yaml"
        )
    engines[EngineType.COMPUTING] = default_engines[EngineType.COMPUTING].lower()
    if engines[EngineType.COMPUTING] not in get_engine_class_members(ComputingEngine):
        raise RuntimeError(f"{engines[EngineType.COMPUTING]} is illegal")

    # federation engine
    if default_engines.get(EngineType.FEDERATION) is not None:
        engines[EngineType.FEDERATION] = default_engines[EngineType.FEDERATION].lower()

    # storage engine
    if default_engines.get(EngineType.STORAGE) is not None:
        engines[EngineType.STORAGE] = default_engines[EngineType.STORAGE].lower()

    # set default storage engine and federation engine by computing engine
    for t in (EngineType.STORAGE, EngineType.FEDERATION):
        if engines.get(t) is None:
            # use default relation engine
            engines[t] = Relationship.Computing[engines[EngineType.COMPUTING]][t][
                "default"
            ]

    # set default federated mode by federation engine
    if engines[EngineType.FEDERATION] == FederationEngine.STANDALONE:
        engines["federated_mode"] = FederatedMode.SINGLE
    else:
        engines["federated_mode"] = FederatedMode.MULTIPLE

    if engines[EngineType.STORAGE] not in get_engine_class_members(StorageEngine):
        raise RuntimeError(f"{engines[EngineType.STORAGE]} is illegal")

    if engines[EngineType.FEDERATION] not in get_engine_class_members(FederationEngine):
        raise RuntimeError(f"{engines[EngineType.FEDERATION]} is illegal")

    for t in [EngineType.FEDERATION]:
        if (
                engines[t]
                not in Relationship.Computing[engines[EngineType.COMPUTING]][t]["support"]
        ):
            raise RuntimeError(
                f"{engines[t]} is not supported in {engines[EngineType.COMPUTING]}"
            )

    return engines


def is_standalone():
    return (
        get_engines().get(EngineType.FEDERATION).lower() == FederationEngine.STANDALONE
    )


def get_engines_config_from_conf(group_map=False):
    engines_config = {}
    for engine_type in {
        EngineType.COMPUTING,
        EngineType.FEDERATION,
        EngineType.STORAGE,
    }:
      engines_config[engine_type] = {}
      for _name, _conf in conf_utils.get_base_config(engine_type, {}).items():
          engines_config[engine_type][_name] = _conf
    return engines_config