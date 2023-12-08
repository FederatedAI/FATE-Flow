from typing import Optional, Dict, List

from pydantic import BaseModel


class InitiatorSpec(BaseModel):
    role: str
    node_id: str


class RoleSpec(BaseModel):
    guest: Optional[List[str]]
    host: Optional[List[str]]
    arbiter: Optional[List[str]]


class JobCommonSpec(BaseModel):
    sync_type: Optional[str] = "poll"


class JobParamsSpec(BaseModel):
    common: Optional[JobCommonSpec]
    guest: Optional[Dict]
    host: Optional[Dict]
    arbiter: Optional[Dict]


class TaskParamsSpec(BaseModel):
    common: Optional[Dict]
    guest: Optional[Dict]
    host: Optional[Dict]
    arbiter: Optional[Dict]


class ConfSpec(BaseModel):
    initiator: InitiatorSpec
    role: RoleSpec
    job_params: JobParamsSpec
    task_params: TaskParamsSpec
    version: str


class DataSpec(BaseModel):
    key: str
    type: str


class DagComponentSpec(BaseModel):
    name: str
    componentName: str
    provider: str
    version: str
    input: Optional[List[DataSpec]] = []
    output: Optional[List[DataSpec]] = []


class DagSpec(BaseModel):
    components: List[DagComponentSpec]
    version: str


class BFIADagSpec(BaseModel):
    config: ConfSpec
    dag: DagSpec
    flow_id: str = ""
    old_job_id: str = ""


class DagSchemaSpec(BaseModel):
    dag: BFIADagSpec
    schema_version: str
    kind: str = "bfia"
