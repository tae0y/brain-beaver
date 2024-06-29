from model import Concepts
from pgvector.sqlalchemy import Vector

def select_nearest_with_top_p(source: Vector, target: list[Concepts]):
    """
    source 컨셉과 target 컨셉간의 유사도를 계산한다
    """
    pass

def select_nearest_with_threshold(source: Vector, target: list[Concepts]):
    """
    source 컨셉과 target 컨셉간의 유사도를 계산한다
    """
    pass