from sqlalchemy import Integer, create_engine
from sqlalchemy import TIMESTAMP
from sqlalchemy import INTEGER
from sqlalchemy import String
from sqlalchemy import Column
from sqlalchemy.orm import declarative_base
Base = declarative_base()


class Service(Base):
    __tablename__ = "metrics"
    name = Column(String, primary_key=True)
    time_serie = Column(INTEGER)
    time = Column(TIMESTAMP, nullable=False, primary_key=True)
    cpu = Column(INTEGER)
    latency = Column(INTEGER)
    replicas = Column(INTEGER)
    memory = Column(INTEGER)

if __name__ == "__main__":
    engine = create_engine(
        "postgresql://postgres:password@localhost:5432/metrics", echo=True)

    Base.metadata.create_all(engine)

    with engine.connect() as con:
        result = con.execute(
            "SELECT create_hypertable('metrics', 'time');")
