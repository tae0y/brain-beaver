from sqlalchemy import Integer, String, Column
from sqlalchemy.orm import declarative_base

Base = declarative_base()

class Networks(Base):
    __tablename__ = 'tb_networks'
    id                     = Column(Integer, primary_key=True, autoincrement=True)
    source_concept_id      = Column(String)
    target_concept_id      = Column(String)

    def __str__(self):
        return f"Networks(id={self.id}, source={self.source}, target={self.target})"
