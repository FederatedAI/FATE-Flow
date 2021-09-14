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
from ._base import BaseEntity


class JobConfigurationBase(BaseEntity):
    def __init__(self, dsl=None, runtime_conf=None, **kwargs):
        self._dsl = dsl if dsl else kwargs.get("job_dsl")
        self._runtime_conf = runtime_conf if runtime_conf else kwargs.get("job_runtime_conf")

    @property
    def dsl(self):
        return self._dsl

    @property
    def runtime_conf(self):
        return self._runtime_conf


class JobConfiguration(JobConfigurationBase):
    def __init__(self, dsl, runtime_conf, runtime_conf_on_party, train_runtime_conf, **kwargs):
        super().__init__(dsl, runtime_conf, **kwargs)
        self._runtime_conf_on_party = runtime_conf_on_party
        self._train_runtime_conf = train_runtime_conf

    @property
    def runtime_conf_on_party(self):
        return self._runtime_conf_on_party

    @property
    def train_runtime_conf(self):
        return self._train_runtime_conf

