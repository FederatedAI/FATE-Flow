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
from fate_flow.entity.types import StandaloneAddress, EggRollAddress, HDFSAddress, MysqlAddress, HiveAddress, \
    PathAddress, ApiAddress, ComputingEngine, StorageEngine, FederationEngine, EngineType, FileAddress


class Relationship(object):
    Computing = {
        ComputingEngine.STANDALONE: {
            EngineType.STORAGE: {
                "default": StorageEngine.STANDALONE,
                "support": [StorageEngine.STANDALONE],
            },
            EngineType.FEDERATION: {
                "default": FederationEngine.STANDALONE,
                "support": [
                    FederationEngine.STANDALONE,
                    FederationEngine.RABBITMQ,
                    FederationEngine.PULSAR,
                    FederationEngine.OSX,
                    FederationEngine.ROLLSITE
                ],
            },
        },
        ComputingEngine.EGGROLL: {
            EngineType.STORAGE: {
                "default": StorageEngine.EGGROLL,
                "support": [StorageEngine.EGGROLL],
            },
            EngineType.FEDERATION: {
                "default": FederationEngine.ROLLSITE,
                "support": [
                    FederationEngine.ROLLSITE,
                    FederationEngine.RABBITMQ,
                    FederationEngine.PULSAR,
                    FederationEngine.OSX
                ],
            },
        },
        ComputingEngine.SPARK: {
            EngineType.STORAGE: {
                "default": StorageEngine.HDFS,
                "support": [
                    StorageEngine.HDFS,
                    StorageEngine.HIVE,
                    StorageEngine.FILE,
                    StorageEngine.STANDALONE
                ],
            },
            EngineType.FEDERATION: {
                "default": FederationEngine.RABBITMQ,
                "support": [FederationEngine.PULSAR, FederationEngine.RABBITMQ, FederationEngine.OSX, FederationEngine.STANDALONE],
            },
        }
    }

    EngineToAddress = {
        StorageEngine.STANDALONE: StandaloneAddress,
        StorageEngine.EGGROLL: EggRollAddress,
        StorageEngine.HDFS: HDFSAddress,
        StorageEngine.MYSQL: MysqlAddress,
        StorageEngine.HIVE: HiveAddress,
        StorageEngine.FILE: FileAddress,
        StorageEngine.PATH: PathAddress,
        StorageEngine.API: ApiAddress
    }

