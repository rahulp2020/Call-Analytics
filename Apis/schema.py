from pydantic import BaseModel
from typing import Optional, List


class CallResponse(BaseModel):
    call_id: str
    agent_id: str
    customer_id: str
    language: Optional[str]
    start_time: Optional[str]
    duration_seconds: Optional[int]
    transcript_customer: Optional[str]
    transcript_agent: Optional[str]
    agent_talk_ratio: Optional[float]
    customer_sentiment_score: Optional[float]
    embeddings: Optional[str]


class PaginatedCallResponse(BaseModel):
    total: int
    offset: int
    limit: int
    data: List[CallResponse]


class AgentStats(BaseModel):
    agent_id: str
    total_calls: int
    avg_talk_ratio: float
    avg_sentiment_score: float


class Itemparams(BaseModel):
    limit: Optional[int] = 10
    offset: Optional[int] = 0
    agent_id: Optional[str] = None
    from_date: Optional[str] = None
    to_date: Optional[str] = None
    min_sentiment: Optional[float] = None
    max_sentiment: Optional[float] = None


class SimilarCall(BaseModel):
    call_id: str
    transcript_agent: Optional[str]
    transcript_customer: Optional[str]


class RecommendationResponse(BaseModel):
    call_id: str
    similar_calls: List[SimilarCall]
    coaching_nudges: List[str]


class UserRequest(BaseModel):
    name: str


class UserResponse(BaseModel):
    name: str
    token: str
