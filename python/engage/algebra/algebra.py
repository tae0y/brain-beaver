from pgvector.sqlalchemy import Vector
import numpy as np
import time

def cosine_similarity(list1, list2) -> float:
    """
    두 벡터간의 코사인 유사도를 계산한다
    """
    begin_time = time.time()

    vector1 = np.array(list1)
    vector2 = np.array(list2)

    dot_product = np.dot(vector1, vector2)

    norm1 = np.linalg.norm(vector1)
    norm2 = np.linalg.norm(vector2)

    cosine_sim = dot_product / (norm1 * norm2)

    end_time = time.time()
    #print(f"cosine_similarity elapsed time: {end_time - begin_time} sec")

    return cosine_sim