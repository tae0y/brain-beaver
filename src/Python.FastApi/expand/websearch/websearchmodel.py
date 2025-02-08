from sqlalchemy import Integer, String, Column, Text
from sqlalchemy.orm import declarative_base

Base = declarative_base()

class WebSearchResult(Base):
    __tablename__ = 'tb_websearch_results'
    id      = Column(Integer, primary_key=True, autoincrement=True)
    query   = Column(String, nullable=False)
    result  = Column(Text)  # 검색 결과 저장

    def __str__(self):
        return f"WebSearchResult(id={self.id}, query={self.query})"
