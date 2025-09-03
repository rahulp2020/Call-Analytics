from sqlalchemy import create_engine, inspect, Column, Integer, String, Float, ForeignKey, DateTime, Text
from sqlalchemy.orm import declarative_base, sessionmaker, relationship

Base = declarative_base()


class Agent(Base):
    __tablename__ = "agents"

    agent_id = Column(String, primary_key=True)
    avg_talk_ratio = Column(Float, default=0.0)
    avg_sentiment_score = Column(Float, default=0.0)
    total_calls = Column(Integer, default=0)

    calls = relationship("Call", back_populates="agent")


class Call(Base):
    __tablename__ = "calls"

    call_id = Column(String, primary_key=True)
    agent_id = Column(String, ForeignKey("agents.agent_id"), index=True)
    customer_id = Column(String, nullable=False)
    language = Column(String, default="en")
    start_time = Column(String, index=True)
    duration_seconds = Column(Integer)
    transcript_customer = Column(Text)
    transcript_agent = Column(Text)

    agent_talk_ratio = Column(Float)
    customer_sentiment_score = Column(Float)
    embeddings = Column(Text)

    agent = relationship("Agent", back_populates="calls")
