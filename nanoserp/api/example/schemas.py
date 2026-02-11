from pydantic import BaseModel


class ExampleRequest(BaseModel):
    data: str


class ExampleResponse(BaseModel):
    message: str
