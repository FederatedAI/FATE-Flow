import json

import grpc

from ..conf import FATE_FLOW_SERVICE_NAME
from ..protobuf.python import basic_meta_pb2, proxy_pb2, proxy_pb2_grpc


def wrap_grpc_packet(json_body, http_method, url, src_party_id, dst_party_id, job_id=None, headers=None, overall_timeout=None):
    _src_end_point = basic_meta_pb2.Endpoint(ip=HOST, port=GRPC_PORT)
    _src = proxy_pb2.Topic(name=job_id, partyId="{}".format(src_party_id), role=FATE_FLOW_SERVICE_NAME,
                           callback=_src_end_point)
    _dst = proxy_pb2.Topic(name=job_id, partyId="{}".format(dst_party_id), role=FATE_FLOW_SERVICE_NAME, callback=None)
    _model = proxy_pb2.Model(name="headers", dataKey=json.dumps(headers))
    _task = proxy_pb2.Task(taskId=job_id, model=_model)
    _command = proxy_pb2.Command(name=url)
    _conf = proxy_pb2.Conf(overallTimeout=overall_timeout)
    _meta = proxy_pb2.Metadata(src=_src, dst=_dst, task=_task, command=_command, operator=http_method, conf=_conf)
    _data = proxy_pb2.Data(key=url, value=bytes(json.dumps(json_body), 'utf-8'))
    return proxy_pb2.Packet(header=_meta, body=_data)


def get_command_federation_channel(host, port):
    channel = grpc.insecure_channel(f"{host}:{port}")
    stub = proxy_pb2_grpc.DataTransferServiceStub(channel)
    return channel, stub


def gen_routing_metadata(src_party_id, dest_party_id):
    routing_head = (
        ("service", "fateflow"),
        ("src-party-id", str(src_party_id)),
        ("src-role", "guest"),
        ("dest-party-id", str(dest_party_id)),
        ("dest-role", "host"),
    )
    return routing_head