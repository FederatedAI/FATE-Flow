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
from functools import reduce

import casbin
import peewee as pw

from fate_flow.db.base_models import singleton, DB
from fate_flow.entity.types import ProcessRole
from fate_flow.runtime.runtime_config import RuntimeConfig
from fate_flow.runtime.system_settings import CASBIN_MODEL_CONF, CASBIN_TABLE_NAME, PERMISSION_TABLE_NAME, \
    PERMISSION_CASBIN_MODEL_CONF


class FlowCasbinAdapter(casbin.persist.Adapter):
    def __init__(self, rule=None):
        if not rule:
            rule = FlowCasbinRule
        self.rule = rule
        self.database = DB
        proxy = pw.Proxy()
        self.rule._meta.database = proxy
        proxy.initialize(DB)

    def load_policy(self, model):
        for line in self.rule.select():
            casbin.persist.load_policy_line(str(line), model)

    def _save_policy_line(self, ptype, rule):
        data = dict(zip(['v0', 'v1', 'v2', 'v3', 'v4', 'v5'], rule))
        item = self.rule(ptype=ptype)
        item.__data__.update(data)
        item.save()

    def save_policy(self, model):
        """saves all policy rules to the storage."""
        for sec in ["p", "g"]:
            if sec not in model.model.keys():
                continue
            for ptype, ast in model.model[sec].items():
                for rule in ast.policy:
                    self._save_policy_line(ptype, rule)
        return True

    def add_policy(self, sec, ptype, rule):
        """adds a policy rule to the storage."""
        self._save_policy_line(ptype, rule)

    def remove_policy(self, sec, ptype, rule):
        """removes a policy rule from the storage."""
        if sec in ["p", "g"]:
            condition = [self.rule.ptype==ptype]
            data = dict(zip(['v0', 'v1', 'v2', 'v3', 'v4', 'v5'], rule))
            condition.extend([getattr(self.rule, k) == data[k] for k in data])
            check = self.rule.select().filter(*condition)
            if check.exists():
                self.rule.delete().where(*condition).execute()
                return True
            else:
                return False
        else:
            return False

    def remove_filtered_policy(self, sec, ptype, field_index, *field_values):
        """removes policy rules that match the filter from the storage.
        This is part of the Auto-Save feature.
        """
        pass


class FlowCasbinRule(pw.Model):
    class Meta:
        table_name = CASBIN_TABLE_NAME
    ptype = pw.CharField(max_length=255, null=True)
    v0 = pw.CharField(max_length=255, null=True)
    v1 = pw.CharField(max_length=255, null=True)
    v2 = pw.CharField(max_length=255, null=True)
    v3 = pw.CharField(max_length=255, null=True)
    v4 = pw.CharField(max_length=255, null=True)
    v5 = pw.CharField(max_length=255, null=True)

    def __str__(self):
        return reduce(lambda x, y: str(x) + ', ' + str(y) if y else x,
                      [self.ptype, self.v0, self.v1, self.v2, self.v3, self.v4, self.v5])

    def __repr__(self):
        if not self.id:
            return "<{cls}: {desc}>".format(cls=self.__class__.__name__, desc=self)
        return "<{cls} {pk}: {desc}>".format(cls=self.__class__.__name__, pk=self.id, desc=self)


class PermissionCasbinRule(pw.Model):
    class Meta:
        table_name = PERMISSION_TABLE_NAME
    ptype = pw.CharField(max_length=255, null=True)
    v0 = pw.CharField(max_length=255, null=True)
    v1 = pw.CharField(max_length=255, null=True)
    v2 = pw.CharField(max_length=255, null=True)
    v3 = pw.CharField(max_length=255, null=True)
    v4 = pw.CharField(max_length=255, null=True)
    v5 = pw.CharField(max_length=255, null=True)

    def __str__(self):
        return reduce(lambda x, y: str(x) + ', ' + str(y) if y else x,
                      [self.ptype, self.v0, self.v1, self.v2, self.v3, self.v4, self.v5])

    def __repr__(self):
        if not self.id:
            return "<{cls}: {desc}>".format(cls=self.__class__.__name__, desc=self)
        return "<{cls} {pk}: {desc}>".format(cls=self.__class__.__name__, pk=self.id, desc=self)


class FlowEnforcer(casbin.Enforcer):
    @property
    def reload_policy(self):
        self.load_policy()
        return self


@singleton
class FateCasbin(object):
    def __init__(self):
        self.adapter = None
        self.init_adapter()
        self._e = FlowEnforcer(CASBIN_MODEL_CONF, self.adapter)

    def init_adapter(self):
        self.adapter = FlowCasbinAdapter()
        self.init_table()

    @staticmethod
    def init_table():
        FlowCasbinRule.create_table()

    @property
    def re(self) -> casbin.Enforcer:
        return self._e.reload_policy

    @property
    def e(self) -> casbin.Enforcer:
        return self._e

    def add_policy(self, role, resource, permission):
        return self.e.add_policy(role, resource, permission)

    def remove_policy(self, role, resource, permission):
        return self.e.remove_policy(role, resource, permission)

    def add_role_for_user(self, user, role):
        return self.e.add_role_for_user(user, role)

    def delete_role_for_suer(self, user, role):
        return self.e.delete_role_for_user(user, role)

    def delete_roles_for_user(self, user):
        return self.e.delete_roles_for_user(user)

    def delete_user(self, user):
        return self.e.delete_user(user)

    def delete_role(self, role):
        return self.e.delete_role(role)

    def delete_permission(self, *permission):
        return self.e.delete_permission(*permission)

    def delete_permissions_for_user(self, user):
        return self.e.delete_permissions_for_user(user)

    def get_roles_for_user(self, user):
        return self.re.get_roles_for_user(user)

    def get_users_for_role(self, role):
        return self.re.get_users_for_role(role)

    def has_role_for_user(self, user, role):
        return self.re.has_role_for_user(user, role)

    def has_permission_for_user(self, user, *permission):
        return self.re.has_permission_for_user(user, *permission)

    def get_permissions_for_user(self, user):
        return self.re.get_permissions_for_user(user)

    def enforcer(self, *rvals):
        return self.re.enforce(*rvals)


@singleton
class PermissionCasbin(object):
    def __init__(self):
        self.adapter = None
        self.init_adapter()
        self._e = FlowEnforcer(PERMISSION_CASBIN_MODEL_CONF, self.adapter)

    def init_adapter(self):
        self.adapter = FlowCasbinAdapter(rule=PermissionCasbinRule)
        self.init_table()

    @staticmethod
    def init_table():
        PermissionCasbinRule.create_table()

    @property
    def re(self) -> casbin.Enforcer:
        return self._e.reload_policy

    @property
    def e(self) -> casbin.Enforcer:
        return self._e

    def query(self, party_id):
        return self.re.get_permissions_for_user(party_id)

    def delete(self, party_id, type, value):
        return self.re.delete_permission_for_user(party_id, type, value)

    def delete_all(self, party_id, type):
        return self.re.remove_filtered_policy(0, party_id, type)

    def grant(self, party_id, type, value):
        return self.re.add_permission_for_user(party_id, type, value)

    def enforce(self, party_id, type, value):
        try:
            return self.re.enforce(party_id, type, str(value))
        except Exception as e:
            raise Exception(f"{party_id}, {type}, {value} {e}")


if RuntimeConfig.PROCESS_ROLE == ProcessRole.DRIVER:
    FATE_CASBIN = FateCasbin()
    PERMISSION_CASBIN = PermissionCasbin()
else:
    FATE_CASBIN = None
    PERMISSION_CASBIN = None
