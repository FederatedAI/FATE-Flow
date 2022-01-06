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
import operator
from functools import reduce
from typing import Dict, Type, Union

from fate_flow.db.db_models import DB, DataBaseModel
from fate_flow.db.runtime_config import RuntimeConfig
from fate_flow.utils.log_utils import getLogger


LOGGER = getLogger()


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


# https://docs.peewee-orm.com/en/latest/peewee/query_operators.html
supported_operators = {
    '==': operator.eq,
    '<': operator.lt,
    '<=': operator.le,
    '>': operator.gt,
    '>=': operator.ge,
    '!=': operator.ne,
    '<<': operator.lshift,
    '>>': operator.rshift,
    '%': operator.mod,
    '**': operator.pow,
    '^': operator.xor,
    '~': operator.inv,
}
'''
query = {
    # Job.f_job_id == '1234567890'
    'job_id': '1234567890',
    # Job.f_party_id == 999
    'party_id': 999,
    # Job.f_tag != 'submit_failed'
    'tag': ('!=', 'submit_failed'),
    # Job.f_status.in_(['success', 'running', 'waiting'])
    'status': ('in_', ['success', 'running', 'waiting']),
    # Job.f_create_time.between(10000, 99999)
    'create_time': ('between', 10000, 99999),
    # Job.f_description.distinct()
    'description': ('distinct', ),
}
'''
def query_dict2expression(model: Type[DataBaseModel], query: Dict[str, Union[bool, int, str, list, tuple]]):
    expression = []

    for field, value in query.items():
        if not isinstance(value, (list, tuple)):
            value = ('==', value)
        op, *val = value

        field = getattr(model, f'f_{field}')
        value = supported_operators[op](field, val[0]) if op in supported_operators else getattr(field, op)(*val)
        expression.append(value)

    return reduce(operator.iand, expression)


def query_db(model: Type[DataBaseModel], limit: int = 0, offset: int = 0,
             query: dict = None, order_by: Union[str, list, tuple] = None):
    data = model.select()
    if query:
        data = data.where(query_dict2expression(model, query))
    count = data.count()

    if not order_by:
        order_by = 'create_time'
    if not isinstance(order_by, (list, tuple)):
        order_by = (order_by, 'asc')
    order_by, order = order_by
    order_by = getattr(model, f'f_{order_by}')
    order_by = getattr(order_by, order)()
    data = data.order_by(order_by)

    if limit > 0:
        data = data.limit(limit)
    if offset > 0:
        data = data.offset(offset)

    return list(data), count
