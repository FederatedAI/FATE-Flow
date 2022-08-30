import casbin
import casbin_sqlalchemy_adapter
import pymysql

from fate_flow.db.db_models import singleton
from fate_flow.settings import CASBIN_MODEL_CONF, DATABASE, CASBIN_TABLE_NAME, PERMISSION_SWITCH
from sqlalchemy import Column, Integer, String, TEXT, create_engine

pymysql.install_as_MySQLdb()

class FateCasbinRule(casbin_sqlalchemy_adapter.Base):
    __tablename__ = CASBIN_TABLE_NAME

    id = Column(Integer, primary_key=True)
    ptype = Column(String(255))
    v0 = Column(String(255))
    v1 = Column(String(255))
    v2 = Column(TEXT())
    v3 = Column(Integer())
    v4 = Column(String(255))
    v5 = Column(String(255))

    def __str__(self):
        arr = [self.ptype]
        for v in (self.v0, self.v1, self.v2, self.v3, self.v4, self.v5):
            if v is None:
                break
            arr.append(v)
        return ", ".join(arr)

    def __repr__(self):
        return '<FateCasbinRule {}: "{}">'.format(self.id, str(self))


@singleton
class FateCasbin():
    def __init__(self):
        self.engine = create_engine(
            f"mysql://{DATABASE.get('user')}:{DATABASE.get('passwd')}@{DATABASE.get('host')}:{DATABASE.get('port')}/{DATABASE.get('name')}")
        self.adapter = casbin_sqlalchemy_adapter.Adapter(self.engine, FateCasbinRule)
        self.e = casbin.Enforcer(CASBIN_MODEL_CONF, self.adapter)

    def query(self, party_id):
        self.e.load_policy()
        return self.e.get_permissions_for_user(party_id)

    def delete(self, party_id, type, value):
        self.e.load_policy()
        return self.e.delete_permission_for_user(party_id, type, value)

    def delete_all(self, party_id, type):
        self.e.load_policy()
        return self.e.remove_filtered_policy(0, party_id, type)

    def grant(self, party_id, type, value):
        self.e.load_policy()
        return self.e.add_permission_for_user(party_id, type, value)

    def enforce(self, party_id, type, value):
        self.e.load_policy()
        try:
            return self.e.enforce(party_id, type, str(value))
        except Exception as e:
            raise Exception(f"{party_id}, {type}, {value} {e}")


CB = FateCasbin() if PERMISSION_SWITCH else None