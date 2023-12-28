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
import json

import grpc

from ..proto.rollsite import basic_meta_pb2, proxy_pb2, proxy_pb2_grpc


def wrap_proxy_grpc_packet(json_body, http_method, url, src_party_id, dst_party_id, job_id=None, headers=None,
                           overall_timeout=None, role="fateflow", source_host=None, source_port=None):
    if not headers:
        headers = {}
    _src_end_point = basic_meta_pb2.Endpoint(ip=source_host, port=source_port)
    _src = proxy_pb2.Topic(name=job_id, partyId="{}".format(src_party_id), role=role,
                           callback=_src_end_point)
    _dst = proxy_pb2.Topic(name=job_id, partyId="{}".format(dst_party_id), role=role, callback=None)
    _model = proxy_pb2.Model(name="headers", dataKey=json.dumps(headers))
    _task = proxy_pb2.Task(taskId=job_id, model=_model)
    _command = proxy_pb2.Command(name=url)
    _conf = proxy_pb2.Conf(overallTimeout=overall_timeout)
    _meta = proxy_pb2.Metadata(src=_src, dst=_dst, task=_task, command=_command, operator=http_method, conf=_conf)
    _data = proxy_pb2.Data(key=url, value=bytes(json.dumps(json_body), 'utf-8'))
    return proxy_pb2.Packet(header=_meta, body=_data)


def get_proxy_channel(host, port):
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