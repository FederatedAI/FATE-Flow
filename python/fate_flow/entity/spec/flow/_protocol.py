from typing import Optional, Dict, Any, List

import pydantic

from fate_flow.entity.spec.dag import DAGSchema


class SubmitJobInput(pydantic.BaseModel):
    dag_schema: DAGSchema


class SubmitJobOutput(pydantic.BaseModel):
    message: str = "success"
    code: int = 0
    job_id: str
    data: Optional[Dict[str, Any]] = {}


class QueryJobInput(pydantic.BaseModel):
    jobs: List[Any]


class QueryJobOutput(pydantic.BaseModel):
    jobs: List[Any]


class StopJobInput(pydantic.BaseModel):
    job_id: str


class StopJobOutput(pydantic.BaseModel):
    message: str = "success"
    code: int = 0


class QueryTaskInput(pydantic.BaseModel):
    tasks: List[Any]


class QueryTaskOutput(pydantic.BaseModel):
    tasks: List[Any]
