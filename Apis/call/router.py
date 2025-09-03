import json
from datetime import datetime

import numpy as np
import openai
from fastapi import HTTPException
from fastapi import APIRouter, Depends, Query
from typing import List, Optional

from sqlalchemy.orm import Session

from Models.model import Call
from Apis.schema import CallResponse, PaginatedCallResponse, Itemparams, RecommendationResponse, SimilarCall
from Apis.dependency import get_db

router = APIRouter()


def cosine_similarity(vec1: list[float], vec2: list[float]) -> float:
    v1 = np.array(vec1)
    v2 = np.array(vec2)
    if np.linalg.norm(v1) == 0 or np.linalg.norm(v2) == 0:
        return 0.0
    return float(np.dot(v1, v2) / (np.linalg.norm(v1) * np.linalg.norm(v2)))


def get_call_embeddings(call) -> Optional[list[float]]:
    if not call.embeddings:
        return None
    try:
        return json.loads(call.embeddings)
    except Exception as e:
        return None


def generate_coaching_nudges(agent_transcript: str) -> list[str]:
    if not agent_transcript:
        return [
            "hello",
            "hi",
            "hey"
        ]

    try:
        prompt = (
            "You are a call center coach. Read this agent transcript:\n\n"
            f"{agent_transcript}\n\n"
            "Generate 3 short coaching nudges (≤40 words each) to help the agent improve."
        )

        response = openai.ChatCompletion.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=120,
        )

        nudges_text = response["choices"][0]["message"]["content"]
        nudges = [n.strip() for n in nudges_text.split("\n") if n.strip()]
        return nudges[:3]  # only top 3
    except Exception as e:
        return [
            "hello",
            "hi",
            "hey"
        ]


@router.get("/", response_model=PaginatedCallResponse)
async def get_calls(params: Itemparams = Depends(), session: Session = Depends(get_db)):
    try:
        query = session.query(Call)

        if params.agent_id:
            query = query.filter(Call.agent_id == params.agent_id)

        if params.from_date:
            try:
                datetime.fromisoformat(params.from_date)
                query = query.filter(Call.start_time >= params.from_date)
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid from_date format. Use YYYY-MM-DD")

        if params.to_date:
            try:
                datetime.fromisoformat(params.to_date)
                query = query.filter(Call.start_time <= params.to_date)
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid to_date format. Use YYYY-MM-DD")

        if params.min_sentiment is not None:
            query = query.filter(Call.customer_sentiment_score >= params.min_sentiment)
        if params.max_sentiment is not None:
            query = query.filter(Call.customer_sentiment_score <= params.max_sentiment)

        total = query.count()
        calls = query.offset(params.offset).limit(params.limit).all()
        if not calls:
            return PaginatedCallResponse(total=0, limit=params.limit, offset=params.offset, data=[])
        data = [
            CallResponse(
                call_id=c.call_id,
                agent_id=c.agent_id,
                customer_id=c.customer_id,
                language=c.language,
                start_time=c.start_time,
                duration_seconds=c.duration_seconds,
                transcript_customer=c.transcript_customer,
                transcript_agent=c.transcript_agent,
                agent_talk_ratio=c.agent_talk_ratio,
                customer_sentiment_score=c.customer_sentiment_score,
                embeddings=c.embeddings,
            )
            for c in calls
        ]

        return PaginatedCallResponse(
            total=total,
            limit=params.limit,
            offset=params.offset + len(calls),
            data=data
        )
    finally:
        session.close()


@router.get("/{call_id}", response_model=CallResponse)
async def get_call(call_id: str, session: Session = Depends(get_db)):
    call = session.query(Call).filter_by(call_id=call_id).first()
    if not call:
        raise HTTPException(status_code=400, detail=f"Call {call_id} not found")
    return call


@router.get("/{call_id}/recommendations", response_model=RecommendationResponse)
async def get_recommendations(call_id: str, session: Session = Depends(get_db)):
    main_call = session.query(Call).filter(Call.call_id == call_id).first()
    if not main_call:
        raise HTTPException(status_code=404, detail="Call not found")

    main_vec = get_call_embeddings(main_call)
    if not main_vec:
        raise HTTPException(status_code=400, detail="Embeddings missing for this call")

    calls = session.query(Call).filter(Call.call_id != call_id).all()
    if not calls:
        return RecommendationResponse(call_id=call_id, similar_calls=[], coaching_nudges=[])
    similarities = []
    for c in calls:
        vec = get_call_embeddings(c)
        if vec:
            sim = cosine_similarity(main_vec, vec)
            similarities.append((c, sim))

    top_5 = sorted(similarities, key=lambda x: x[1], reverse=True)[:5]

    similar_calls = [
        SimilarCall(
            call_id=c.call_id,
            transcript_agent=c.transcript_agent,
            transcript_customer=c.transcript_customer,
        )
        for c, _ in top_5
    ]

    nudges = generate_coaching_nudges(main_call.transcript_agent)

    return RecommendationResponse(
        call_id=call_id,
        similar_calls=similar_calls,
        coaching_nudges=nudges,
    )
