from pydantic import BaseModel


class DrugEventReaction(BaseModel):
    reaction: str
    count: int


class DrugEventSearchResponse(BaseModel):
    query: str
    count: int
    limit: int
    source_name: str
    endpoint: str
    retrieval_timestamp: str
    medical_disclaimer: str
    faers_disclaimer: str
    top_reactions: list[DrugEventReaction]