from fate_flow.entity.code import ReturnCode


class ParametersBase:
    def to_dict(self):
        d = {}
        for k, v in self.__dict__.items():
            d[k] = v
        return d


class AuthenticationParameters(ParametersBase):
    def __init__(self, path, method, headers, form, data, json, full_path):
        self.path = path
        self.method = method
        self.headers = headers
        self.form = form
        self.data = data
        self.json = json
        self.full_path = full_path


class AuthenticationReturn(ParametersBase):
    def __init__(self, code=ReturnCode.Base.SUCCESS, message="success"):
        self.code = code
        self.message = message


class SignatureParameters(ParametersBase):
    def __init__(self, party_id, body, initiator_party_id=""):
        self.party_id = party_id
        self.initiator_party_id = initiator_party_id
        self.body = body


class SignatureReturn(ParametersBase):
    def __init__(self, code=ReturnCode.Base.SUCCESS, signature=None, message=""):
        self.code = code
        self.signature = signature
        self.message = message


class PermissionCheckParameters(ParametersBase):
    def __init__(self, initiator_party_id, roles, component_list, dataset_list, dag_schema, component_parameters):
        self.party_id = initiator_party_id
        self.roles = roles
        self.component_list = component_list
        self.dataset_list = dataset_list
        self.dag_schema = dag_schema
        self.component_parameters = component_parameters


class PermissionReturn(ParametersBase):
    def __init__(self, code=ReturnCode.Base.SUCCESS, message="success"):
        self.code = code
        self.message = message


