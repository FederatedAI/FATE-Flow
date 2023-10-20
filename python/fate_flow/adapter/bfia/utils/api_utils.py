from flask import jsonify

from fate_flow.adapter.bfia.utils.entity.code import ReturnCode
from fate_flow.utils.api_utils import API


class BfiaAPI(API):
    class Output:
        @staticmethod
        def json(code=ReturnCode.SUCCESS, msg='success', data=None, **kwargs):
            result_dict = {
                "code": code,
                "msg": msg,
                "data": data,
            }

            response = {}
            for key, value in result_dict.items():
                if value is not None:
                    response[key] = value
            # extra resp
            for key, value in kwargs.items():
                response[key] = value
            return jsonify(response)