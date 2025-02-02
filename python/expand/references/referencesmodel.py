from sqlalchemy import Integer, String, Column
from sqlalchemy.orm import declarative_base

Base = declarative_base()

class References(Base):
    __tablename__ = 'tb_references'
    id                     = Column(Integer, primary_key=True, autoincrement=True)
    concept_id       = Column(String)
    description      = Column(String)

    def __str__(self):
        return f"References(id={self.id}, source={self.concept_id}, target={self.description})"