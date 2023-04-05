from pydantic import BaseModel


class AvailableGroupsResponseModel(BaseModel):
    groups: list[str]
