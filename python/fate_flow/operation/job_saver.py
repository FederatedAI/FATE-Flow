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
import time
import typing

from fate_arch.common.base_utils import current_timestamp
from fate_flow.db.db_models import DB, Job, Task, DataBaseModel
from fate_flow.entity.run_status import JobStatus, TaskStatus, EndStatus
from fate_flow.utils.log_utils import schedule_logger, sql_logger
from fate_flow.utils import schedule_utils
import peewee


class JobSaver(object):
    STATUS_FIELDS = ["status", "party_status"]

    @classmethod
    def create_job(cls, job_info) -> Job:
        return cls.create_job_family_entity(Job, job_info)

    @classmethod
    def create_task(cls, task_info) -> Task:
        return cls.create_job_family_entity(Task, task_info)

    @classmethod
    @DB.connection_context()
    def delete_job(cls, job_id):
        Job.delete().where(Job.f_job_id == job_id)

    @classmethod
    def update_job_status(cls, job_info):
        schedule_logger(job_info["job_id"]).info("try to update job status to {}".format(job_info.get("status")))
        update_status = cls.update_status(Job, job_info)
        if update_status:
            schedule_logger(job_info["job_id"]).info("update job status successfully")
            if EndStatus.contains(job_info.get("status")):
                new_job_info = {}
                # only update tag
                for k in ["job_id", "role", "party_id", "tag"]:
                    if k in job_info:
                        new_job_info[k] = job_info[k]
                if not new_job_info.get("tag"):
                    new_job_info["tag"] = "job_end"
                cls.update_entity_table(Job, new_job_info)
        else:
            schedule_logger(job_info["job_id"]).warning("update job status does not take effect")
        return update_status

    @classmethod
    def update_job(cls, job_info):
        schedule_logger(job_info["job_id"]).info("try to update job")
        if "status" in job_info:
            # Avoid unintentional usage that updates the status
            del job_info["status"]
            schedule_logger(job_info["job_id"]).warning("try to update job, pop job status")
        update_status = cls.update_entity_table(Job, job_info)
        if update_status:
            schedule_logger(job_info.get("job_id")).info(f"job update successfully: {job_info}")
        else:
            schedule_logger(job_info.get("job_id")).warning(f"job update does not take effect: {job_info}")
        return update_status

    @classmethod
    def update_task_status(cls, task_info):
        schedule_logger(task_info["job_id"]).info("try to update task {} {} status".format(task_info["task_id"], task_info["task_version"]))
        update_status = cls.update_status(Task, task_info)
        if update_status:
            schedule_logger(task_info["job_id"]).info("update task {} {} status successfully: {}".format(task_info["task_id"], task_info["task_version"], task_info))
        else:
            schedule_logger(task_info["job_id"]).warning("update task {} {} status update does not take effect: {}".format(task_info["task_id"], task_info["task_version"], task_info))
        return update_status

    @classmethod
    def update_task(cls, task_info):
        schedule_logger(task_info["job_id"]).info("try to update task {} {}".format(task_info["task_id"], task_info["task_version"]))
        update_status = cls.update_entity_table(Task, task_info)
        if update_status:
            schedule_logger(task_info["job_id"]).info("task {} {} update successfully".format(task_info["task_id"], task_info["task_version"]))
        else:
            schedule_logger(task_info["job_id"]).warning("task {} {} update does not take effect".format(task_info["task_id"], task_info["task_version"]))
        return update_status

    @classmethod
    def reload_task(cls, source_task, target_task):
        task_info = {"job_id": target_task.f_job_id, "task_id": target_task.f_task_id, "task_version": target_task.f_task_version,
                     "role": target_task.f_role, "party_id": target_task.f_party_id}
        update_info = {}
        update_list = ["cmd", "elapsed", "end_date", "end_time", "engine_conf", "party_status", "run_ip",
                       "run_pid", "start_date", "start_time", "status", "worker_id"]
        for k in update_list:
            update_info[k] = getattr(source_task, f"f_{k}")
        task_info.update(update_info)
        schedule_logger(task_info["job_id"]).info("try to update task {} {}".format(task_info["task_id"], task_info["task_version"]))
        schedule_logger(task_info["job_id"]).info("update info: {}".format(update_info))
        update_status = cls.update_entity_table(Task, task_info)
        if update_status:
            cls.update_task_status(task_info)
            schedule_logger(task_info["job_id"]).info("task {} {} update successfully".format(task_info["task_id"], task_info["task_version"]))
        else:
            schedule_logger(task_info["job_id"]).warning("task {} {} update does not take effect".format(task_info["task_id"], task_info["task_version"]))
        return update_status

    @classmethod
    @DB.connection_context()
    def create_job_family_entity(cls, entity_model, entity_info):
        obj = entity_model()
        obj.f_create_time = current_timestamp()
        for k, v in entity_info.items():
            attr_name = 'f_%s' % k
            if hasattr(entity_model, attr_name):
                setattr(obj, attr_name, v)
        try:
            rows = obj.save(force_insert=True)
            if rows != 1:
                raise Exception("Create {} failed".format(entity_model))
            return obj
        except peewee.IntegrityError as e:
            if e.args[0] == 1062 or (isinstance(e.args[0], str) and "UNIQUE constraint failed" in e.args[0]):
                sql_logger(job_id=entity_info.get("job_id", "fate_flow")).warning(e)
            else:
                raise Exception("Create {} failed:\n{}".format(entity_model, e))
        except Exception as e:
            raise Exception("Create {} failed:\n{}".format(entity_model, e))

    @classmethod
    @DB.connection_context()
    def update_status(cls, entity_model: DataBaseModel, entity_info: dict):
        query_filters = []
        primary_keys = entity_model.get_primary_keys_name()
        for p_k in primary_keys:
            query_filters.append(operator.attrgetter(p_k)(entity_model) == entity_info[p_k.lstrip("f").lstrip("_")])
        objs = entity_model.select().where(*query_filters)
        if objs:
            obj = objs[0]
        else:
            raise Exception(f"can not found the {entity_model.__name__} record to update")
        update_filters = query_filters[:]
        update_info = {"job_id": entity_info["job_id"]}
        for status_field in cls.STATUS_FIELDS:
            if entity_info.get(status_field) and hasattr(entity_model, f"f_{status_field}"):
                if status_field in ["status", "party_status"]:
                    update_info[status_field] = entity_info[status_field]
                    old_status = getattr(obj, f"f_{status_field}")
                    new_status = update_info[status_field]
                    if_pass = False
                    if isinstance(obj, Task):
                        if TaskStatus.StateTransitionRule.if_pass(src_status=old_status, dest_status=new_status):
                            if_pass = True
                    elif isinstance(obj, Job):
                        if JobStatus.StateTransitionRule.if_pass(src_status=old_status, dest_status=new_status):
                            if_pass = True
                        if EndStatus.contains(new_status) and new_status not in {JobStatus.SUCCESS, JobStatus.CANCELED}:
                            update_filters.append(Job.f_rerun_signal == False)
                    if if_pass:
                        update_filters.append(operator.attrgetter(f"f_{status_field}")(type(obj)) == old_status)
                    else:
                        # not allow update status
                        update_info.pop(status_field)
        return cls.execute_update(old_obj=obj, model=entity_model, update_info=update_info, update_filters=update_filters)

    @classmethod
    @DB.connection_context()
    def update_entity_table(cls, entity_model, entity_info):
        query_filters = []
        primary_keys = entity_model.get_primary_keys_name()
        for p_k in primary_keys:
            query_filters.append(operator.attrgetter(p_k)(entity_model) == entity_info[p_k.lstrip("f").lstrip("_")])
        objs = entity_model.select().where(*query_filters)
        if objs:
            obj = objs[0]
        else:
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
    def query_job(cls, reverse=None, order_by=None, **kwargs):
        return Job.query(reverse=reverse, order_by=order_by, **kwargs)

    @classmethod
    @DB.connection_context()
    def get_tasks_asc(cls, job_id, role, party_id):
        tasks = Task.query(order_by="create_time", reverse=False, job_id=job_id, role=role, party_id=party_id)
        tasks_group = cls.get_latest_tasks(tasks=tasks)
        return tasks_group

    @classmethod
    @DB.connection_context()
    def query_task(cls, only_latest=True, reverse=None, order_by=None, **kwargs) -> typing.List[Task]:
        tasks = Task.query(reverse=reverse, order_by=order_by, **kwargs)
        if only_latest:
            tasks_group = cls.get_latest_tasks(tasks=tasks)
            return list(tasks_group.values())
        else:
            return tasks

    @classmethod
    @DB.connection_context()
    def check_task(cls, job_id, role, party_id, components: list):
        filters = [
            Task.f_job_id == job_id,
            Task.f_role == role,
            Task.f_party_id == party_id,
            Task.f_component_name << components
        ]
        tasks = Task.select().where(*filters)
        if tasks and len(tasks) == len(components):
            return True
        else:
            return False

    @classmethod
    def get_latest_tasks(cls, tasks):
        tasks_group = {}
        for task in tasks:
            task_key = cls.task_key(task_id=task.f_task_id, role=task.f_role, party_id=task.f_party_id)
            if task_key not in tasks_group:
                tasks_group[task_key] = task
            elif task.f_task_version > tasks_group[task_key].f_task_version:
                # update new version task
                tasks_group[task_key] = task
        return tasks_group

    @classmethod
    def fill_job_inference_dsl(cls, job_id, role, party_id, dsl_parser, origin_inference_dsl):
        # must fill dsl for fate serving
        components_parameters = {}
        tasks = cls.query_task(job_id=job_id, role=role, party_id=party_id, only_latest=True)
        for task in tasks:
            components_parameters[task.f_component_name] = task.f_component_parameters
        return schedule_utils.fill_inference_dsl(dsl_parser, origin_inference_dsl=origin_inference_dsl, components_parameters=components_parameters)

    @classmethod
    def task_key(cls, task_id, role, party_id):
        return f"{task_id}_{role}_{party_id}"


def str_to_time_stamp(time_str):
    time_array = time.strptime(time_str, "%Y-%m-%d %H:%M:%S")
    time_stamp = int(time.mktime(time_array) * 1000)
    return time_stamp
