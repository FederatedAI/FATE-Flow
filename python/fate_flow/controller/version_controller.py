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

# algorithm version compatibility control
from fate_arch.common import file_utils
from fate_flow.settings import INCOMPATIBLE_VERSION_CONF


class VersionController:
    INCOMPATIBLE_VERSION = {}

    @classmethod
    def init(cls):
        try:
            conf = file_utils.load_yaml_conf(INCOMPATIBLE_VERSION_CONF)
            for key, key_version in conf.items():
                cls.INCOMPATIBLE_VERSION[key] = {}
                for version in conf[key]:
                    cls.INCOMPATIBLE_VERSION[key][str(version)] = conf[key][version]
        except Exception as e:
            pass

    @classmethod
    def job_provider_version_check(cls, providers_info, local_role, local_party_id):
        incompatible_info = {}
        incompatible = False
        if local_role in providers_info:
            local_provider = providers_info[local_role].get(int(local_party_id), {}) \
                             or providers_info[local_role].get(str(local_party_id), {})
            for role, role_provider in providers_info.items():
                incompatible_info[role] = {}
                for party_id, provider in role_provider.items():
                    if role == local_role and str(party_id) == str(local_party_id):
                        continue
                    role_incompatible_info = cls.provider_version_check(local_provider, party_provider=provider)
                    if role_incompatible_info:
                        incompatible = True
                        incompatible_info[role][party_id] = role_incompatible_info
        if incompatible:
            raise ValueError(f"version compatibility check failed: {incompatible_info}")

    @classmethod
    def provider_version_check(cls, local_provider, party_provider):
        incompatible_info = {}
        for component, info in local_provider.items():
            if party_provider.get(component):
                local_version = local_provider.get(component).get("provider").get("version")
                party_version = party_provider.get(component).get("provider").get("version")
                if cls.is_incompatible(local_version, party_version):
                    if component in incompatible_info:
                        incompatible_info[component].append((local_version, party_version))
                    else:
                        incompatible_info[component] = [(local_version, party_version)]
        return incompatible_info

    @classmethod
    def is_incompatible(cls, source_version, dest_version, key="FATE"):
        if not source_version or not dest_version:
            return False
        index = len(source_version)
        while True:
            if source_version[:index] in cls.INCOMPATIBLE_VERSION.get(key, {}).keys():
                for incompatible_value in cls.INCOMPATIBLE_VERSION.get(key)[source_version[:index]].split(","):
                    if cls.is_match(dest_version, incompatible_value.strip()):
                        return True
            index -= 1
            if index == 0:
                return False

    @classmethod
    def is_match(cls, dest_ver, incompatible_value):
        symbols, incompatible_ver = cls.extract_symbols(incompatible_value)
        dest_ver_list = cls.extend_version([int(_) for _ in dest_ver.split(".")])
        incompatible_ver_list = cls.extend_version([int(_) for _ in incompatible_ver.split(".")])
        print(dest_ver_list, incompatible_ver_list, symbols)
        for index in range(4):
            if dest_ver_list[index] == incompatible_ver_list[index]:
                continue
            if dest_ver_list[index] > incompatible_ver_list[index]:
                return True if ">" in symbols else False
            if dest_ver_list[index] < incompatible_ver_list[index]:
                return True if "<" in symbols else False
        return True if "=" in symbols else False

    @classmethod
    def extend_version(cls, v):
        v_len = len(v)
        if v_len < 4:
            for i in range(4 - v_len):
                v.append(0)
        return v

    @classmethod
    def extract_symbols(cls, incompatible_value):
        symbols_list = ["<", ">", "="]
        index = 0
        for index, ver in enumerate(incompatible_value):
            if ver not in symbols_list:
                break
        symbol = incompatible_value[0: index]
        if not incompatible_value[0: index]:
            symbol = "="
        return symbol, incompatible_value[index:]
