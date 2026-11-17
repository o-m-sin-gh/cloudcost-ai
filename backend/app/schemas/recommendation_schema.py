from pydantic import BaseModel


class OptimizerStatus(BaseModel):
    status: str
    message: str
