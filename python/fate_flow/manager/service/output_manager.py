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
from typing import List

from fate_flow.db.base_models import BaseModelOperate
from fate_flow.db.db_models import TrackingOutputInfo
from fate_flow.utils.wraps_utils import filter_parameters


class OutputDataTracking(BaseModelOperate):
    @classmethod
    def create(cls, entity_info):
        cls._create_entity(TrackingOutputInfo, entity_info)

    @classmethod
    @filter_parameters()
    def query(cls, reverse=False, **kwargs) -> List[TrackingOutputInfo]:
        return cls._query(TrackingOutputInfo, reverse=reverse, order_by="index", **kwargs)
