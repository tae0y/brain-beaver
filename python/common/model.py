from pgvector.sqlalchemy import Vector
from sqlalchemy import Integer, String, DateTime, Date, Column
from sqlalchemy.orm import declarative_base, mapped_column, Mapped
import datetime

Base = declarative_base()

class Concepts(Base):
    __tablename__ = 'tb_concepts'
    #id : Mapped[int] = mapped_column(Integer, primary_key=True)
    #id         = mapped_column(Integer, primary_key=True)
    id          = Column(Integer, primary_key=True, autoincrement=True)
    title       = Column(String)
    keywords    = Column(String)
    category    = Column(String)
    summary     = Column(String)
    status      = Column(String)
    filepath    = Column(String)
    create_time = Column(DateTime)
    update_time = Column(DateTime)
    token_num   = Column(Integer)
    embedding   = Column(Vector(3072))

    def __str__(self):
        return f"Concepts(id={self.id}, title={self.title}, keywords={self.keywords}, category={self.category}, summary={self.summary}, status={self.status}, filepath={self.filepath}, create_time={self.create_time}, update_time={self.update_time}, token_num={self.token_num}, embedding={self.embedding})"

class Networks(Base):
    __tablename__ = 'tb_networks'
    id          = Column(Integer, primary_key=True, autoincrement=True)
    source      = Column(String)
    target      = Column(String)

    def __str__(self):
        return f"Networks(id={self.id}, source={self.source}, target={self.target})"