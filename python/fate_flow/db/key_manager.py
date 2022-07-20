from Crypto.PublicKey import RSA
from Crypto import Random

from fate_flow.db.db_models import DB, SiteKeyInfo
from fate_flow.entity.types import SiteKeyName
from fate_flow.settings import SITE_AUTHENTICATION, PARTY_ID


def rsa_key_generate():
    random_generator = Random.new().read
    rsa = RSA.generate(2048, random_generator)
    private_pem = rsa.exportKey().decode()
    public_pem = rsa.publickey().exportKey().decode()
    return private_pem, public_pem


class RsaKeyManager:
    @classmethod
    def init(cls):
        if PARTY_ID and SITE_AUTHENTICATION:
            if not cls.get_key(PARTY_ID, key_name=SiteKeyName.PRIVATE.value):
                cls.generate_key(PARTY_ID)

    @classmethod
    @DB.connection_context()
    def create_or_update(cls, party_id, key, key_name=SiteKeyName.PUBLIC.value):
        defaults = {
            "f_party_id": party_id,
            "f_key_name": key_name,
            "f_key": key
        }
        entity_model, status = SiteKeyInfo.get_or_create(
            f_party_id=party_id,
            f_key_name=key_name,
            defaults=defaults
        )
        if status is False:
            for key in defaults:
                setattr(entity_model, key, defaults[key])
            entity_model.save(force_insert=False)
            return "update success"
        else:
            return "save success"

    @classmethod
    def generate_key(cls, party_id):
        private_key, public_key = rsa_key_generate()
        cls.create_or_update(party_id, private_key, key_name=SiteKeyName.PRIVATE.value)
        cls.create_or_update(party_id, public_key, key_name=SiteKeyName.PUBLIC.value)

    @classmethod
    @DB.connection_context()
    def get_key(cls, party_id, key_name=SiteKeyName.PUBLIC.value):
        site_info = SiteKeyInfo.query(party_id=party_id, key_name=key_name)
        if site_info:
            return site_info[0].f_key
        else:
            return None

    @classmethod
    @DB.connection_context()
    def get_key(cls, party_id, key_name=SiteKeyName.PUBLIC.value):
        site_info = SiteKeyInfo.query(party_id=party_id, key_name=key_name)
        if site_info:
            return site_info[0].f_key
        else:
            return None

    @classmethod
    @DB.connection_context()
    def delete(cls, party_id, key_name=SiteKeyName.PUBLIC.value):
        site_info = SiteKeyInfo.query(party_id=party_id, key_name=key_name)
        if site_info:
            return site_info[0].delete_instance()
        else:
            return None
