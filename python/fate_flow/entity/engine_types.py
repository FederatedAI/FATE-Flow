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
    LOCALFS = "localfs"
    API = "api"


class CoordinationProxyService(object):
    ROLLSITE = "rollsite"
    NGINX = "nginx"
    FATEFLOW = "fateflow"
    FIREWORK = "firework"
    OSX = "osx"


class FederatedCommunicationType(object):
    PUSH = "PUSH"
    PULL = "PULL"


class GRPCChannel(object):
    DEFAULT = "default"
    OSX = "osx"
