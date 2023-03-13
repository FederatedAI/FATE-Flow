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
from peewee import CharField, CompositeKey

from fate_flow.db import DataBaseModel


class AppInfo(DataBaseModel):
    f_app_name = CharField(max_length=100, index=True)
    f_app_id = CharField(max_length=100, primary_key=True)
    f_app_token = CharField(max_length=100)
    f_app_type = CharField(max_length=20, index=True)

    class Meta:
        db_table = "t_app_info"


class PartnerAppInfo(DataBaseModel):
    f_party_id = CharField(max_length=100, primary_key=True)
    f_app_id = CharField(max_length=100)
    f_app_token = CharField(max_length=100)

    class Meta:
        db_table = "t_partner_app_info"
