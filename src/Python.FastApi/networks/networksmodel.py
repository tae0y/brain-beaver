from sqlalchemy import Integer, String, Column
from sqlalchemy.orm import declarative_base

Base = declarative_base()

class Networks(Base):
    __tablename__ = 'tb_networks'
    id                     = Column(Integer, primary_key=True, autoincrement=True)
    source_concept_id      = Column(String)
    target_concept_id      = Column(String)

    def to_dict(self):
        return {
            "id": self.id,
            "source_concept_id": self.source_concept_id,
            "target_concept_id": self.target_concept_id
        }

    def __repr__(self):
        return str(self.to_dict())

    def __str__(self):
        return str(self.to_dict())
