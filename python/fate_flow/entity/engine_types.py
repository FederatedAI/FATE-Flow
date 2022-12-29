class EngineType(object):
    COMPUTING = "computing"
    STORAGE = "storage"
    FEDERATION = "federation"


class FederationEngine(object):
    EGGROLL = "EGGROLL"
    RABBITMQ = "RABBITMQ"
    STANDALONE = "STANDALONE"
    PULSAR = "PULSAR"


class ComputingEngine(object):
    EGGROLL = "EGGROLL"
    SPARK = "SPARK"
    LINKIS_SPARK = "LINKIS_SPARK"
    STANDALONE = "STANDALONE"


class StorageEngine(object):
    STANDALONE = "STANDALONE"
    EGGROLL = "EGGROLL"
    HDFS = "HDFS"
    MYSQL = "MYSQL"
    SIMPLE = "SIMPLE"
    PATH = "PATH"
    HIVE = "HIVE"
    LINKIS_HIVE = "LINKIS_HIVE"
    LOCALFS = "LOCALFS"
    API = "API"


class CoordinationProxyService(object):
    ROLLSITE = "rollsite"
    NGINX = "nginx"
    FATEFLOW = "fateflow"
    FIREWORK = "firework"


class FederatedCommunicationType(object):
    PUSH = "PUSH"
    PULL = "PULL"
