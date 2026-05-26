from pydantic import BaseModel

class QueryResponse(BaseModel):
    generated_sql: str
    data: dict