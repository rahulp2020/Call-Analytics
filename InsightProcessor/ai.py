import json
from transformers import pipeline
from sentence_transformers import SentenceTransformer
from Models.model import Call, Agent
from Database.database import DBManager


class AIProcessor:
    def __init__(self):
        self.db = DBManager.get_instance()
        self._model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')
        self._sentiment = pipeline("sentiment-analysis")

    def _compute_agent_talk_ratio(self, customer_text: str, agent_text: str) -> float:
        agent_words = len(agent_text.split()) if agent_text else 0
        customer_words = len(customer_text.split()) if customer_text else 0
        total_words = agent_words + customer_words
        return round(agent_words / total_words,2) if total_words > 0 else 0.0

    def _compute_customer_sentiment(self, customer_text: str) -> float:
        if not customer_text:
            return 0.0
        result = self._sentiment(customer_text)[0]
        score = result['score'] if result['label'].upper() == 'POSITIVE' else -result['score']
        return round(score, 2)

    def _compute_embeddings(self, customer_text: str, agent_text: str) -> str:
        text = agent_text + " " + customer_text
        emb = self._model.encode(text)
        emb_small = [round(float(x), 2) for x in emb[:2]]
        return json.dumps(emb_small)

    def _update_agent_metrics(self, call_data: dict):
        with self.db.get_session() as session:
            agent = session.query(Agent).filter_by(agent_id=call_data.get('agent_id')).with_for_update().first()
            if not agent:
                return

            agent.total_calls = agent.total_calls + 1
            agent.avg_talk_ratio = ((agent.avg_talk_ratio * (
                    agent.total_calls - 1)) + call_data.get('agent_talk_ratio')) / agent.total_calls
            agent.avg_sentiment_score = ((agent.avg_sentiment_score * (
                    agent.total_calls - 1)) + call_data.get('customer_sentiment_score')) / agent.total_calls

            session.add(agent)
            session.commit()

    def _run_transaction(self, call_data: dict):
        with self.db.get_session() as session:
            call = Call(
                call_id=call_data.get("call_id"),
                agent_id=call_data.get("agent_id"),
                customer_id=call_data.get("customer_id"),
                language=call_data.get("language", "en"),
                start_time=call_data.get("start_time"),
                duration_seconds=call_data.get("duration_seconds", 0),
                transcript_customer=call_data.get('transcript_customer'),
                transcript_agent=call_data.get('transcript_agent'),
                agent_talk_ratio=call_data.get('agent_talk_ratio'),
                customer_sentiment_score=call_data.get('customer_sentiment_score'),
                embeddings=call_data.get('embeddings')
            )
            agent = session.query(Agent).filter_by(agent_id=call_data.get('agent_id')).first()

            if not agent:
                agent = Agent(agent_id=call_data.get('agent_id'))
                session.add(agent)
                session.flush()
            session.add(call)
            session.commit()

    def process_call_data(self, call_data: dict):
        try:
            transcript = call_data.get("transcript", {})
            customer_text = transcript.get("customer", "")
            agent_text = transcript.get("agent", "")
            agent_talk_ratio = self._compute_agent_talk_ratio(customer_text, agent_text)
            customer_sentiment_score = self._compute_customer_sentiment(customer_text)
            embeddings = self._compute_embeddings(customer_text, agent_text)
            call_data['agent_talk_ratio'] = agent_talk_ratio
            call_data['customer_sentiment_score'] = customer_sentiment_score
            call_data['embeddings'] = embeddings
            call_data['transcript_customer'] = customer_text
            call_data['transcript_agent'] = agent_text
            self._run_transaction(call_data)
            self._update_agent_metrics(call_data)
            print(f"Processed call {call_data.get('call_id')}")
        except Exception as e:
            raise Exception(f"Error processing call data: {e}")

