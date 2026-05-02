from pydantic import BaseModel


class SourceRecord(BaseModel):
    source_id: str
    source_name: str
    endpoint: str
    module: str
    description: str
    update_cadence: str


class SourceRegistryResponse(BaseModel):
    count: int
    sources: list[SourceRecord]