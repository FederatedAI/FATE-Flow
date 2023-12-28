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
from fate_flow.errors.server_error import ResponseException
from fate_flow.proto.rollsite import proxy_pb2_grpc, basic_meta_pb2, proxy_pb2

from fate_flow.runtime.runtime_config import RuntimeConfig
from fate_flow.runtime.system_settings import FATE_FLOW_SERVICE_NAME, GRPC_PORT, HOST, REMOTE_REQUEST_TIMEOUT
from fate_flow.utils.base_utils import json_loads, json_dumps
from fate_flow.utils.log_utils import audit_logger
from fate_flow.utils.requests_utils import request


def gen_routing_metadata(src_party_id, dest_party_id):
    routing_head = (
        ("service", "fateflow"),
        ("src-party-id", str(src_party_id)),
        ("src-role", "guest"),
        ("dest-party-id", str(dest_party_id)),
        ("dest-role", "host"),
    )
    return routing_head


def wrap_grpc_packet(json_body, http_method, url, src_party_id, dst_party_id, job_id=None, headers=None,
                     overall_timeout=REMOTE_REQUEST_TIMEOUT):
    _src_end_point = basic_meta_pb2.Endpoint(ip=HOST, port=GRPC_PORT)
    _src = proxy_pb2.Topic(name=job_id, partyId="{}".format(src_party_id), role=FATE_FLOW_SERVICE_NAME, callback=_src_end_point)
    _dst = proxy_pb2.Topic(name=job_id, partyId="{}".format(dst_party_id), role=FATE_FLOW_SERVICE_NAME, callback=None)
    _model = proxy_pb2.Model(name="headers", dataKey=json_dumps(headers))
    _task = proxy_pb2.Task(taskId=job_id, model=_model)
    _command = proxy_pb2.Command(name=url)
    _conf = proxy_pb2.Conf(overallTimeout=overall_timeout)
    _meta = proxy_pb2.Metadata(src=_src, dst=_dst, task=_task, command=_command, operator=http_method, conf=_conf)
    _data = proxy_pb2.Data(key=url, value=bytes(json_dumps(json_body), 'utf-8'))
    return proxy_pb2.Packet(header=_meta, body=_data)


def get_url(_suffix):
    return "http://{}:{}/{}".format(RuntimeConfig.JOB_SERVER_HOST, RuntimeConfig.HTTP_PORT, _suffix.lstrip('/'))


class UnaryService(proxy_pb2_grpc.DataTransferServiceServicer):
    def unaryCall(self, _request, context):
        packet = _request
        header = packet.header
        _suffix = packet.body.key
        param_bytes = packet.body.value
        param = bytes.decode(param_bytes)
        job_id = header.task.taskId
        src = header.src
        dst = header.dst
        headers_str = header.task.model.dataKey if header.task.model.dataKey else "{}"
        headers = json_loads(headers_str)
        method = header.operator
        param_dict = json_loads(param)
        source_routing_header = []
        for key, value in context.invocation_metadata():
            source_routing_header.append((key, value))

        _routing_metadata = gen_routing_metadata(src_party_id=src.partyId, dest_party_id=dst.partyId)
        context.set_trailing_metadata(trailing_metadata=_routing_metadata)
        audit_logger(job_id).info("rpc receive headers: {}".format(headers))
        audit_logger(job_id).info('rpc receive: {}'.format(packet))
        audit_logger(job_id).info("rpc receive: {} {}".format(get_url(_suffix), param))
        resp = request(method=method, url=get_url(_suffix), json=param_dict, headers=headers)
        audit_logger(job_id).info(f"resp: {resp.text}")
        resp_json = response_json(resp)
        return wrap_grpc_packet(resp_json, method, _suffix, dst.partyId, src.partyId, job_id)


def response_json(response):
    try:
        return response.json()
    except:
        audit_logger().exception(response.text)
        e = ResponseException(response=response.text)
        return {"code": e.code, "message": e.message}

