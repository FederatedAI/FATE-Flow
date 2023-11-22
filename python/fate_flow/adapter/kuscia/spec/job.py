from typing import List, Optional, Union, Dict
from pydantic import BaseModel


class MetadataSpec(BaseModel):
    name: str


class PartySpec(BaseModel):
    domainID: str


# class TaskInputConfigSpec(BaseModel):
#     sf_datasource_config: Dict[str, Dict[str, str]]
#     sf_cluster_desc: Dict
#     sf_node_eval_param: Dict
#     sf_output_uris: List[str]
#     sf_output_ids: List[str]


class TaskSpec(BaseModel):
    alias: str
    taskID: str
    priority: int
    # taskInputConfig: TaskInputConfigSpec
    taskInputConfig: str
    appImage: str
    parties: List[PartySpec]


class KusciaJobSpec(BaseModel):
    initiator: str
    scheduleMode: str
    maxParallelism: int
    tasks: List[TaskSpec]


class DagSchemaSpec(BaseModel):
    apiVersion: str
    kind: str
    metadata: MetadataSpec
    spec: KusciaJobSpec