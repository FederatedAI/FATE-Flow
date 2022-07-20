from fate_flow.entity import RetCode


class ParametersBase:
    def to_dict(self):
        d = {}
        for k, v in self.__dict__.items():
            d[k] = v
        return d


class ClientAuthenticationParameters(ParametersBase):
    def __init__(self, full_path, headers, form, data, json):
        self.full_path = full_path
        self.headers = headers
        self.form = form
        self.data = data
        self.json = json


class ClientAuthenticationReturn(ParametersBase):
    def __init__(self, code=RetCode.SUCCESS, message="success"):
        self.code = code
        self.message = message


class SignatureParameters(ParametersBase):
    def __init__(self, party_id, body):
        self.party_id = party_id
        self.body = body


class SignatureReturn(ParametersBase):
    def __init__(self, code=RetCode.SUCCESS, site_signature=None):
        self.code = code
        self.site_signature = site_signature


class AuthenticationParameters(ParametersBase):
    def __init__(self, src_party_id, site_signature, body):
        self.src_party_id = src_party_id
        self.site_signature = site_signature
        self.body = body


class AuthenticationReturn(ParametersBase):
    def __init__(self, code=RetCode.SUCCESS, message="success"):
        self.code = code
        self.message = message


class PermissionCheckParameters(ParametersBase):
    def __init__(self, src_role, src_party_id, role, party_id, initiator, roles, component_list, dataset_list, runtime_conf, dsl, component_parameters):
        self.src_role = src_role
        self.src_party_id = src_party_id
        self.role = role
        self.party_id = party_id
        self.initiator = initiator
        self.roles = roles
        self.component_list = component_list
        self.dataset_list = dataset_list
        self.run_time_conf = runtime_conf
        self.dsl = dsl
        self.component_parameters = component_parameters


class PermissionReturn(ParametersBase):
    def __init__(self, code=RetCode.SUCCESS, message="success"):
        self.code = code
        self.message = message


