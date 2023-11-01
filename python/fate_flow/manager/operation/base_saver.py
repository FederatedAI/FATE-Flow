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
from typing import Type, Union, Dict

from fate_flow.db.base_models import DB, BaseModelOperate, DataBaseModel
from fate_flow.db.db_models import Task, Job
from fate_flow.db.schedule_models import ScheduleTask, ScheduleTaskStatus, ScheduleJob
from fate_flow.entity.types import JobStatus, TaskStatus, EndStatus
from fate_flow.errors.server_error import NoFoundJob, NoFoundTask
from fate_flow.utils.base_utils import current_timestamp
from fate_flow.utils.log_utils import schedule_logger, sql_logger


class BaseSaver(BaseModelOperate):
    STATUS_FIELDS = ["status", "party_status"]
    OPERATION = {
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

    @classmethod
    def _create_job(cls, job_obj, job_info):
        return cls._create_entity(job_obj, job_info)

    @classmethod
    def _create_task(cls, task_obj, task_info):
        return cls._create_entity(task_obj, task_info)

    @classmethod
    @DB.connection_context()
    def _delete_job(cls, job_obj, job_id):
        _op = job_obj.delete().where(job_obj.f_job_id == job_id)
        return _op.execute() > 0

    @classmethod
    def _update_job_status(cls, job_obj, job_info):
        schedule_logger(job_info["job_id"]).info("try to update job status to {}".format(job_info.get("status")))
        update_status = cls._update_status(job_obj, job_info)
        if update_status:
            schedule_logger(job_info["job_id"]).info("update job status successfully")
            if cls.end_status_contains(job_info.get("status")):
                new_job_info = {}
                # only update tag
                for k in ["job_id", "role", "party_id", "tag"]:
                    if k in job_info:
                        new_job_info[k] = job_info[k]
                if not new_job_info.get("tag"):
                    new_job_info["tag"] = "job_end"
                cls.update_entity_table(job_obj, new_job_info)
        else:
            schedule_logger(job_info["job_id"]).warning("update job status does not take effect")
        return update_status

    @classmethod
    def _update_job(cls, job_obj, job_info):
        schedule_logger(job_info["job_id"]).info("try to update job")
        if "status" in job_info:
            # Avoid unintentional usage that updates the status
            del job_info["status"]
            schedule_logger(job_info["job_id"]).warning("try to update job, pop job status")
        update_status = cls.update_entity_table(job_obj, job_info)
        if update_status:
            schedule_logger(job_info.get("job_id")).info(f"job update successfully: {job_info}")
        else:
            schedule_logger(job_info.get("job_id")).warning(f"job update does not take effect: {job_info}")
        return update_status

    @classmethod
    def _update_task_status(cls, task_obj, task_info):
        schedule_logger(task_info["job_id"]).info("try to update task {} {} status".format(task_info["task_id"],
                                                                                           task_info["task_version"]))
        update_status = cls._update_status(task_obj, task_info)
        if update_status:
            schedule_logger(task_info["job_id"]).info("update task {} {} status successfully: {}".format(task_info["task_id"], task_info["task_version"], task_info))
        else:
            schedule_logger(task_info["job_id"]).warning("update task {} {} status update does not take effect: {}".format(task_info["task_id"], task_info["task_version"], task_info))
        return update_status

    @classmethod
    def _update_task(cls, task_obj, task_info, report=False):
        schedule_logger(task_info["job_id"]).info("try to update task {} {}".format(task_info["task_id"],
                                                                                    task_info["task_version"]))
        update_status = cls.update_entity_table(task_obj, task_info)
        if task_info.get("error_report") and report:
            schedule_logger(task_info["job_id"]).error("role {} party id {} task {} error report: {}".format(
                task_info["role"], task_info["party_id"], task_info["task_id"], task_info["error_report"]))
        if update_status:
            schedule_logger(task_info["job_id"]).info("task {} {} update successfully".format(task_info["task_id"], task_info["task_version"]))
        else:
            schedule_logger(task_info["job_id"]).warning("task {} {} update does not take effect".format(task_info["task_id"], task_info["task_version"]))
        return update_status

    @classmethod
    @DB.connection_context()
    def _update_status(cls, entity_model, entity_info: dict):
        query_filters = []
        primary_keys = entity_model.get_primary_keys_name()
        for p_k in primary_keys:
            query_filters.append(operator.attrgetter(p_k)(entity_model) == entity_info[p_k[2:]])

        objs = entity_model.select().where(*query_filters)
        if not objs:
            raise Exception(f"can not found the {entity_model.__name__} record to update")
        obj = objs[0]

        update_filters = query_filters.copy()
        update_info = {"job_id": entity_info["job_id"]}

        for status_field in cls.STATUS_FIELDS:
            if entity_info.get(status_field) and hasattr(entity_model, f"f_{status_field}"):
                if status_field in ["status", "party_status"]:
                    # update end time
                    if hasattr(obj, "f_start_time") and obj.f_start_time:
                        if cls.end_status_contains(entity_info.get(status_field)):
                            update_info["end_time"] = current_timestamp()
                            update_info['elapsed'] = update_info['end_time'] - obj.f_start_time
                    update_info[status_field] = entity_info[status_field]
                    old_status = getattr(obj, f"f_{status_field}")
                    new_status = update_info[status_field]
                    if_pass = False
                    if isinstance(obj, Task) or isinstance(obj, ScheduleTask) or isinstance(obj, ScheduleTaskStatus):
                        if cls.check_task_status(old_status, new_status):
                            if_pass = True
                    elif isinstance(obj, Job) or isinstance(obj, ScheduleJob):
                        if cls.check_job_status(old_status, new_status):
                            if_pass = True
                        if cls.end_status_contains(new_status) and new_status not in {JobStatus.SUCCESS, JobStatus.CANCELED}:
                            if isinstance(obj, ScheduleJob):
                                update_filters.append(ScheduleJob.f_rerun_signal==False)
                    if if_pass:
                        update_filters.append(operator.attrgetter(f"f_{status_field}")(type(obj)) == old_status)
                    else:
                        # not allow update status
                        update_info.pop(status_field)

        return cls.execute_update(old_obj=obj, model=entity_model, update_info=update_info, update_filters=update_filters)

    @classmethod
    def check_task_status(cls, old_status, dest_status):
        return TaskStatus.StateTransitionRule.if_pass(src_status=old_status, dest_status=dest_status)

    @classmethod
    def check_job_status(cls, old_status, dest_status):
        return JobStatus.StateTransitionRule.if_pass(src_status=old_status, dest_status=dest_status)

    @classmethod
    def end_status_contains(cls, status):
        return EndStatus.contains(status)

    @classmethod
    @DB.connection_context()
    def update_entity_table(cls, entity_model, entity_info, filters: list = None):
        query_filters = []
        primary_keys = entity_model.get_primary_keys_name()
        if not filters:
            for p_k in primary_keys:
                query_filters.append(operator.attrgetter(p_k)(entity_model) == entity_info[p_k.lstrip("f").lstrip("_")])
        else:
            for _k in filters:
                p_k = f"f_{_k}"
                query_filters.append(operator.attrgetter(p_k)(entity_model) == entity_info[_k])
        objs = entity_model.select().where(*query_filters)
        if objs:
            obj = objs[0]
        else:
            if entity_model.__name__ == Job.__name__:
                raise NoFoundJob()
            if entity_model.__name__ == Job.__name__:
                raise NoFoundTask()
            raise Exception("can not found the {}".format(entity_model.__name__))
        update_filters = query_filters[:]
        update_info = {}
        update_info.update(entity_info)
        for _ in cls.STATUS_FIELDS:
            # not allow update status fields by this function
            update_info.pop(_, None)
        if update_info.get("tag") in {"job_end", "submit_failed"} and hasattr(entity_model, "f_tag"):
            if obj.f_start_time:
                update_info["end_time"] = current_timestamp()
                update_info['elapsed'] = update_info['end_time'] - obj.f_start_time
        if update_info.get("progress") and hasattr(entity_model, "f_progress") and update_info["progress"] > 0:
            update_filters.append(operator.attrgetter("f_progress")(entity_model) <= update_info["progress"])
        return cls.execute_update(old_obj=obj, model=entity_model, update_info=update_info, update_filters=update_filters)

    @classmethod
    def execute_update(cls, old_obj, model, update_info, update_filters):
        update_fields = {}
        for k, v in update_info.items():
            attr_name = 'f_%s' % k
            if hasattr(model, attr_name) and attr_name not in model.get_primary_keys_name():
                update_fields[operator.attrgetter(attr_name)(model)] = v
        if update_fields:
            if update_filters:
                operate = old_obj.update(update_fields).where(*update_filters)
            else:
                operate = old_obj.update(update_fields)
            sql_logger(job_id=update_info.get("job_id", "fate_flow")).info(operate)
            return operate.execute() > 0
        else:
            return False

    @classmethod
    @DB.connection_context()
    def _query_job(cls, job_obj, reverse=None, order_by=None, **kwargs):
        return job_obj.query(reverse=reverse, order_by=order_by, **kwargs)

    @classmethod
    @DB.connection_context()
    def _query_task(cls, task_obj, only_latest=True, reverse=None, order_by=None, scheduler_status=False, **kwargs):
        tasks = task_obj.query(reverse=reverse, order_by=order_by, **kwargs)
        if only_latest:
            tasks_group = cls.get_latest_tasks(tasks=tasks, scheduler_status=scheduler_status)
            return list(tasks_group.values())
        else:
            return tasks

    @classmethod
    def get_latest_tasks(cls, tasks, scheduler_status=False):
        tasks_group = {}
        for task in tasks:
            task_key = cls.task_key(task_id=task.f_task_id, role=task.f_role, party_id=task.f_party_id) if not scheduler_status else task.f_task_name
            if task_key not in tasks_group:
                tasks_group[task_key] = task
            elif task.f_task_version > tasks_group[task_key].f_task_version:
                # update new version task
                tasks_group[task_key] = task
        return tasks_group

    @classmethod
    def task_key(cls, task_id, role, party_id):
        return f"{task_id}_{role}_{party_id}"

    @classmethod
    def get_latest_scheduler_tasks(cls, tasks):
        tasks_group = {}
        for task in tasks:
            if task.f_task_id not in tasks_group:
                tasks_group[task.f_task_id] = task
            elif task.f_task_version > tasks_group[task.f_task_id].f_task_version:
                tasks_group[task.f_task_id] = task
        return tasks_group

    @classmethod
    @DB.connection_context()
    def _list(cls, model: Type[DataBaseModel], limit: int = 0, offset: int = 0,
              query: dict = None, order_by: Union[str, list, tuple] = None):
        data = model.select()
        if query:
            data = data.where(cls.query_dict2expression(model, query))
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

    @classmethod
    def query_dict2expression(cls, model: Type[DataBaseModel], query: Dict[str, Union[bool, int, str, list, tuple]]):
        expression = []
        for field, value in query.items():
            if not isinstance(value, (list, tuple)):
                value = ('==', value)
            op, *val = value

            field = getattr(model, f'f_{field}')
            value = cls.OPERATION[op](field, val[0]) if op in cls.OPERATION else getattr(field, op)(*val)

            expression.append(value)

        return reduce(operator.iand, expression)

    @property
    def supported_operators(self):
        return