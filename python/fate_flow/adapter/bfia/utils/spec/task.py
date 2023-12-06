from typing import Optional, Dict

from pydantic import BaseModel

from fate_flow.adapter.bfia.utils.spec.artifact import ArtifactAddress


class RuntimeConf(BaseModel):
    name: str
    parameter: Dict = {}
    input: Optional[Dict[str, ArtifactAddress]]
    output: Optional[Dict[str, ArtifactAddress]]


class RuntimeComponent(BaseModel):
    component: RuntimeConf


class LogPath(BaseModel):
    path: str


class Config(BaseModel):
    task_id: str
    trace_id: Optional[str]
    session_id: str = ""
    token: str = ""
    inst_id: Dict
    node_id: Dict
    log: Optional[LogPath]
    self_role: str


class SystemConf(BaseModel):
    storage: str
    transport: str
    callback: str


class TaskRuntimeEnv(BaseModel):
    runtime: RuntimeComponent
    config: Config
    system: SystemConf
