from fastapi import APIRouter, Depends
from typing import List

from sqlalchemy.orm import Session

from Apis.schema import AgentStats
from Models.model import Agent
from fastapi import HTTPException
from Apis.dependency import get_db

router = APIRouter()


@router.get("/agents", response_model=List[AgentStats])
async def get_agent_leaderboard(session: Session = Depends(get_db)):
    agents = session.query(Agent).order_by(Agent.avg_sentiment_score.desc(), Agent.avg_talk_ratio.desc(),
                                           Agent.total_calls.desc())
    if not agents:
        raise HTTPException(status_code=404, detail="No agents found")

    result = []
    for agent in agents:
        result.append(
            AgentStats(
                agent_id=agent.agent_id,
                total_calls=agent.total_calls or 0,
                avg_talk_ratio=agent.avg_talk_ratio or 0.0,
                avg_sentiment_score=agent.avg_sentiment_score or 0.0
            )
        )
    return result
