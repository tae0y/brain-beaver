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

    def __str__(self):
        return f"Concepts(id={self.id}, title={self.title}, keywords={self.keywords}, category={self.category}, summary={self.summary}, status={self.status}, filepath={self.filepath}, source_num={self.source_num}, target_num={self.target_num}, create_time={self.create_time}, update_time={self.update_time}, token_num={self.token_num}, plaintext={self.plaintext[:40]}, embedding={self.embedding[:10]})"
