#!/usr/bin/env python
# -*- coding: utf-8 -*-

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

# Todo: let it go
from fate_flow.components.param.param_extract import ParamExtract

# Todo: add module and cpn for better error message


class BaseParam(object):
    def __init__(self):
        pass

    def set_name(self, name: str):
        self._name = name
        return self

    def check(self):
        raise NotImplementedError("Parameter Object should have be check")

    def as_dict(self):
        return ParamExtract().change_param_to_dict(self)

    @classmethod
    def from_dict(cls, conf):
        obj = cls()
        obj.update(conf)
        return obj

    def update(self, conf, allow_redundant=False):
        return ParamExtract().recursive_parse_param_from_config(
            param=self,
            config_json=conf,
            param_parse_depth=0,
            valid_check=not allow_redundant,
            name=self._name,
        )
