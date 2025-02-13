from sqlalchemy import Integer, String, Column, Text
from sqlalchemy.orm import declarative_base

Base = declarative_base()

class References(Base):
    __tablename__ = 'tb_references'
    id                     = Column(Integer, primary_key=True, autoincrement=True)
    concept_id       = Column(String)
    description      = Column(String)

    def to_dict(self):
        return {
            "id": self.id,
            "concept_id": self.concept_id,
            "description": self.description
        }

    def __repr__(self):
        return str(self.to_dict())

    def __str__(self):
        return str(self.to_dict())