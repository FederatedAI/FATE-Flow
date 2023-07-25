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
class EngineType(object):
    COMPUTING = "computing"
    STORAGE = "storage"
    FEDERATION = "federation"


class FederationEngine(object):
    ROLLSITE = "rollsite"
    RABBITMQ = "rabbitmq"
    STANDALONE = "standalone"
    PULSAR = "pulsar"
    OSX = "osx"


class ComputingEngine(object):
    EGGROLL = "eggroll"
    SPARK = "spark"
    STANDALONE = "standalone"


class StorageEngine(object):
    STANDALONE = "standalone"
    EGGROLL = "eggroll"
    HDFS = "hdfs"
    MYSQL = "mysql"
    SIMPLE = "simple"
    PATH = "path"
    HIVE = "hive"
    FILE = "file"
    API = "api"


class CoordinationProxyService(object):
    ROLLSITE = "rollsite"
    NGINX = "nginx"
    FATEFLOW = "fateflow"
    FIREWORK = "firework"
    OSX = "osx"


class FederatedCommunicationType(object):
    POLL = "poll"
    CALLBACK = "callback"


class LauncherType(object):
    DEFAULT = "default"
    DEEPSPEED = "deepspeed"
