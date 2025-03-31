from pydantic import BaseModel
from typing import Dict, List

class Property(BaseModel):
    type: str
    description: str

class ToolInputSchema(BaseModel):
    type: str = "object"
    properties: Dict[str, Dict[str, Property]]

class Tool(BaseModel):
    name: str
    description: str
    input_schema: ToolInputSchema
    required: List[str]
