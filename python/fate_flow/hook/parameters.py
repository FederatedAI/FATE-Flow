from fate_flow.entity import RetCode


class ParametersBase:
    def to_dict(self):
        d = {}
        for k, v in self.__dict__.items():
            d[k] = v
        return d


class SignatureParameters(ParametersBase):
    def __init__(self, party_id, body):
        self.party_id = party_id
        self.body = body


class SignatureReturn(ParametersBase):
    def __init__(self, signature=None):
        self.signature = signature


class AuthenticationParameters(ParametersBase):
    def __init__(self, sign, body):
        self.sign = sign
        self.body = body


class AuthenticationReturn(ParametersBase):
    def __init__(self, code=RetCode.SUCCESS, message="success"):
        self.code = code
        self.message = message


class PermissionCheckParameters(ParametersBase):
    def __init__(self, src_role, src_party_id, role, party_id, initiator, roles, component_list, dataset_list):
        self.src_role = src_role
        self.src_party_id = src_party_id
        self.role = role
        self.party_id = party_id
        self.initiator = initiator
        self.roles = roles
        self.component_list = component_list
        self.dataset_list = dataset_list


class PermissionReturn(ParametersBase):
    def __init__(self, code=RetCode.SUCCESS, message="success"):
        self.code = code
        self.message = message


