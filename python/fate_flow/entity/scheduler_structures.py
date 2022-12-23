from typing import Any, List, Union, Literal, Dict

from pydantic import BaseModel


class PartySpec(BaseModel):
    role: Union[Literal["guest", "host", "arbiter"]]
    party_id: List[Union[str, int]]


class SchedulerInfoSpec(BaseModel):
    dag: Dict[str, Any]
    parties: List[PartySpec]
    initiator_party_id: str
    scheduler_party_id: str
    federated_status_collect_type: str
    model_id: str
    model_version: Union[str, int]


