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

from fate_arch.common import log
from fate_flow.db.db_models import DB
from fate_flow.db.runtime_config import RuntimeConfig

LOGGER = log.getLogger()


@DB.connection_context()
def bulk_insert_into_db(model, data_source, logger):
    try:
        try:
            DB.create_tables([model])
        except Exception as e:
            logger.exception(e)
        batch_size = 50 if RuntimeConfig.USE_LOCAL_DATABASE else 1000
        for i in range(0, len(data_source), batch_size):
            with DB.atomic():
                model.insert_many(data_source[i:i + batch_size]).execute()
        return len(data_source)
    except Exception as e:
        logger.exception(e)
        return 0


def get_dynamic_db_model(base, job_id):
    return type(base.model(table_index=get_dynamic_tracking_table_index(job_id=job_id)))


def get_dynamic_tracking_table_index(job_id):
    return job_id[:8]


def fill_db_model_object(model_object, human_model_dict):
    for k, v in human_model_dict.items():
        attr_name = 'f_%s' % k
        if hasattr(model_object.__class__, attr_name):
            setattr(model_object, attr_name, v)
    return model_object
