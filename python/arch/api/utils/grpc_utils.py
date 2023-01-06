import json

import grpc

from ... import osx_pb2, osx_pb2_grpc


def wrap_grpc_packet(job_id, json_body, http_method, url, src_party_id, dst_party_id, headers=None, role="fateflow", **kwargs):
    _meta = {
        "TechProviderCode": "FT",
        "SourceNodeID": src_party_id,
        "TargetNodeID": dst_party_id,
        "TargetComponentName": role,
        "TargetMethod": "UNARY_CALL",
        "JobId": job_id
    }
    if not headers:
        headers = {}
    _data = bytes(json.dumps(dict(uri=url, json_body=json_body, headers=headers, method=http_method)), 'utf-8')
    return osx_pb2.Inbound(metadata=_meta, payload=_data)


def get_command_federation_channel(host, port):
    channel = grpc.insecure_channel(f"{host}:{port}")
    stub = osx_pb2_grpc.PrivateTransferProtocolStub(channel)
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