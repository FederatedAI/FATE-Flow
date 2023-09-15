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
from fate_flow.entity.code import ReturnCode
from fate_flow.errors import FateFlowError


class JobParamsError(FateFlowError):
    code = ReturnCode.Job.PARAMS_ERROR
    message = 'Job params error'


class NoFoundJob(FateFlowError):
    code = ReturnCode.Job.NOT_FOUND
    message = 'No found job'


class FileNoFound(FateFlowError):
    code = ReturnCode.File.FILE_NOT_FOUND
    message = 'No found file or dir'


class CreateJobFailed(FateFlowError):
    code = ReturnCode.Job.CREATE_JOB_FAILED
    message = 'Create job failed'


class UpdateJobFailed(FateFlowError):
    code = ReturnCode.Job.UPDATE_FAILED
    message = 'Update job does not take effect'


class KillFailed(FateFlowError):
    code = ReturnCode.Job.KILL_FAILED
    message = "Kill job failed"


class JobResourceException(FateFlowError):
    code = ReturnCode.Job.RESOURCE_EXCEPTION
    message = "Job resource exception"


class InheritanceFailed(FateFlowError):
    code = ReturnCode.Job.INHERITANCE_FAILED
    message = "Inheritance job failed"


class NoFoundTask(FateFlowError):
    code = ReturnCode.Task.NOT_FOUND
    message = "No found task"


class StartTaskFailed(FateFlowError):
    code = ReturnCode.Task.START_FAILED
    message = "Start task failed"


class UpdateTaskFailed(FateFlowError):
    code = ReturnCode.Task.UPDATE_FAILED
    message = "Update task status does not take effect"


class KillTaskFailed(FateFlowError):
    code = ReturnCode.Task.KILL_FAILED
    message = 'Kill task failed'


class TaskResourceException(FateFlowError):
    code = ReturnCode.Task.RESOURCE_EXCEPTION
    message = "Task resource exception"


class NoFoundModelOutput(FateFlowError):
    code = ReturnCode.Task.NO_FOUND_MODEL_OUTPUT
    message = "No found output model"


class IsStandalone(FateFlowError):
    code = ReturnCode.Site.IS_STANDALONE
    message = "Site is standalone"


class DeviceNotSupported(FateFlowError):
    code = ReturnCode.Provider.DEVICE_NOT_SUPPORTED
    message = "Device not supported"


class RequestExpired(FateFlowError):
    code = ReturnCode.API.EXPIRED
    message = "Request has expired"


class InvalidParameter(FateFlowError):
    code = ReturnCode.API.INVALID_PARAMETER
    message = "Invalid parameter"


class NoFoundAppid(FateFlowError):
    code = ReturnCode.API.NO_FOUND_APPID
    message = "No found appid"


class ResponseException(FateFlowError):
    code = ReturnCode.Server.RESPONSE_EXCEPTION
    message = "Response exception"


class NoFoundServer(FateFlowError):
    code = ReturnCode.Server.NO_FOUND
    message = "No found server"


class NoFoundINSTANCE(FateFlowError):
    code = ReturnCode.Server.NO_FOUND_INSTANCE
    message = "No Found Flow Instance"


class NoFoundTable(FateFlowError):
    code = ReturnCode.Table.NO_FOUND
    message = "No found table"


class ExistsTable(FateFlowError):
    code = ReturnCode.Table.EXISTS
    message = "Exists table"


class NoPermission(FateFlowError):
    code = ReturnCode.API.NO_PERMISSION
    message = "No Permission"


class PermissionOperateError(FateFlowError):
    code = ReturnCode.API.PERMISSION_OPERATE_ERROR
    message = "Permission Operate Error"


class NoFoundFile(FateFlowError):
    code = ReturnCode.API.NO_FOUND_FILE
    message = "No Found File"


class RoleTypeError(FateFlowError):
    code = ReturnCode.API.ROLE_TYPE_ERROR
    message = "Role Type Error"
