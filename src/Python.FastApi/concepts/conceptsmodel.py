from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.orm import declarative_base

from pgvector.sqlalchemy import Vector

Base = declarative_base()

class Concepts(Base):
    __tablename__ = 'tb_concepts'
    id          = Column(Integer, primary_key=True, autoincrement=True)
    title       = Column(String)
    keywords    = Column(String)
    category    = Column(String)
    summary     = Column(String)
    status      = Column(String)
    data_name    = Column(String)
    source_num  = Column(Integer)
    target_num  = Column(Integer)
    create_time = Column(DateTime)
    update_time = Column(DateTime)
    embedding   = Column(Vector(4096))

    def to_dict(self):
        return {
            "id": self.id,
            "title": self.title,
            "keywords": self.keywords,
            "category": self.category,
            "summary": self.summary,
            "status": self.status,
            "data_name": self.data_name,
            "source_num": self.source_num,
            "target_num": self.target_num,
            "create_time": self.create_time.isoformat() if self.create_time else None,
            "update_time": self.update_time.isoformat() if self.update_time else None,
            "embedding": self.embedding # 필요에 따라 적절히 변환
        }

    def __repr__(self):
        return str(self.to_dict())

    def __str__(self):
        return str(self.to_dict())