from fate_flow.utils.log_utils import getLogger

try:
    from eggroll.core.proto import basic_meta_pb2
    from eggroll.core.proto import proxy_pb2, proxy_pb2_grpc
except ImportError as e:
    from fate_arch.protobuf.python import basic_meta_pb2
    from fate_arch.protobuf.python import proxy_pb2
    from fate_arch.protobuf.python import proxy_pb2_grpc
