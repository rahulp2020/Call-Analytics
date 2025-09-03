from sqlalchemy import create_engine, inspect
from sqlalchemy.orm import sessionmaker, Session
from Models.model import Base, Agent, Call


class DBManager:
    _instance = None
    _tables_created = False
    _db_url = "sqlite:///analytics.db"

    def __init__(self):
        if DBManager._instance is not None:
            raise Exception("engine already created already exists")

        self._engine = create_engine(DBManager._db_url)
        self._SessionLocal = sessionmaker(bind=self._engine)
        self._create_tables()

    @staticmethod
    def get_instance():
        if DBManager._instance is None:
            DBManager._instance = DBManager()
        return DBManager._instance

    def _create_tables(self):
        if not DBManager._tables_created:
            print("Creating tables if they do not exist...")
            Base.metadata.create_all(bind=self._engine)
            DBManager._tables_created = True
            print("Tables created successfully.")
        else:
            pass

        # inspector = inspect(self._engine)
        # if Agent.__tablename__ not in inspector.get_table_names() or Call.__tablename__ not in inspector.get_table_names():
        #     raise Exception("Tables were not created successfully.")
        #
        # for table_name in inspector.get_table_names():
        #     print(f"Table '{table_name}' exists in the database.")
        #
        #     columns = inspector.get_columns(table_name)
        #     for col in columns:
        #         print(f" - Column: {col['name']} (Type: {col['type']})")

    def get_session(self) -> Session:
        return self._SessionLocal()

    def show_table(self):
        with self._SessionLocal() as session:
            all_calls = session.query(Call).all()
            for call in all_calls:
                print(call.call_id, call.agent_id, call.customer_id, call.customer_sentiment_score)

            all_agents = session.query(Agent).all()
            for agent in all_agents:
                print(agent.agent_id, agent.avg_sentiment_score, agent.avg_talk_ratio, agent.total_calls)
