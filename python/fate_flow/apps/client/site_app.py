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
from webargs import fields

from fate_flow.entity.types import Code, SiteCode, ReturnCode
from fate_flow.settings import PARTY_ID, IS_STANDALONE
from fate_flow.utils.api_utils import get_json_result


@manager.route('/info/query', methods=['GET'])
def query_site_info():
    if not IS_STANDALONE:
        return get_json_result(code=ReturnCode.SITE.SUCCESS, message="success", data={"party_id": PARTY_ID})
    else:
        return get_json_result(code=ReturnCode.SITE.IS_STANDALONE, message="site is standalone")