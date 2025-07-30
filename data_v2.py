from dataclasses import dataclass, field, asdict
from enum import Enum
from typing import Dict, Optional, Literal, List, Callable


class DatasetType(str, Enum):
    DEFAULT = "default"
    INSTRUMENTAL = "instrumental"

@dataclass
class Dataset:
    id: str
    name: str
    nameShort: str

    variables: Dict[str, str]  # variable_id -> file path
    type: DatasetType = DatasetType.DEFAULT
    timeStart: Optional[int] = 0
    timeEnd: Optional[int] = 0
    def as_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "nameShort": self.nameShort,
            "timeStart": self.timeStart,
            "timeEnd": self.timeEnd,
            "variables": list(self.variables.keys())
        }
    def as_one(self,variable_id: str):
        return DatasetIndividual(self.id,self.name,self.nameShort, self.timeStart, self.timeEnd,self.variables[variable_id])
@dataclass
class DatasetIndividual:
    id: str
    name: str
    nameShort: str
    timeStart: Optional[int]
    timeEnd: Optional[int]
    path: str  # variable_id -> file path
    type: DatasetType = DatasetType.DEFAULT
    p_value: str = "None"
    r: str = "None"
    def as_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "nameShort": self.nameShort,
            "timeStart": self.timeStart,
            "timeEnd": self.timeEnd,
        }
@dataclass
class VariableMetadata:
    id: str
    colorMap: str
    name: str
    nameShort: str
    multiplier: float
    trendUnit: str
    annualUnit: str
    datasets: List[str] = field(default_factory=list)  # Empty list by default
    transform_timeseries: Optional[Callable[[float], float]] = None # optional function if values need to be transformed for timeseries representation
    def as_dict(self) -> dict:
        data = asdict(self)
        data.pop("transform_timeseries",None)
        return data