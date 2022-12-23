from typing import Dict, List, Union, Any

from fate_flow.entity import BaseModel


class MetricData(BaseModel):
    namespace: Union[str, None]
    name: str
    type: str
    groups: Dict
    metadata: Dict
    data: Union[List, Dict]
