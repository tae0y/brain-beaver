from typing import Tuple
from sqlalchemy import create_engine, insert, select, update
from sqlalchemy.orm import sessionmaker
from pgvector.sqlalchemy import Vector
from common.model import Base, Concepts, Networks, References
from llm.llmroute import embedd_text
from common.algebra import select_nearest_with_top_p, select_nearest_with_threshold
import traceback

"""
sqlalchemy session 생성
"""
URL = "postgresql://root:root@localhost:5432/bwsdb"
engine = create_engine(URL, echo=False, pool_size=50, max_overflow=0)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

#Base.metadata.dop_all(bind=engine)
#Base.metadata.create_all(bind=engine)

"""
Concepts 테이블 관련 함수
"""
def create_keyconcept_into_tb_concepts(keyconcept_list: list[dict]) -> Tuple[int, str]:
    """
    딕셔너리 리스트를 입력받아 tb_concepts 테이블에 모두 저장한다
    """
    rtncd = 900
    rtnmsg = '실패'

    session = SessionLocal()
    try:
        #print(f"before insert cnt : {session.get(Concepts,1)}")
        #print(f"insert element cnt : {len(keyconcept_list)}")
        session.execute(insert(Concepts), keyconcept_list)
        #print(f"after insert cnt  : {session.get(Concepts,1)}")
        rtncd = 200
        rtnmsg = '성공'
        session.commit()
    except Exception as e:
        traceback.print_exc()
        session.rollback()
        rtncd = 900
        rtnmsg = '실패'
    finally:
        session.close()

    return rtncd, rtnmsg

def read_tb_concepts_all() -> list[Concepts]:
    session = SessionLocal()
    try:
        query = session.query(Concepts)
        rtndata = query.all()
    except Exception as e:
        traceback.print_exc()
        rtndata = []
    finally:
        session.close()
    return rtndata

def read_tb_concepts_by_id(concept_id : int) -> Concepts:
    session = SessionLocal()
    try:
        query = session.query(Concepts).filter(Concepts.id == concept_id)
        rtndata = query.first()
    except Exception as e:
        traceback.print_exc()
        rtndata = None
    finally:
        session.close()
    return rtndata

def read_tb_concepts_nearest_by_embedding(source : Concepts, operation: str, limit: int) -> list[Concepts]:
    session = SessionLocal()
    rtndata = []

    try:
        if operation == 'cosine_distance':
            query_result = session.scalars(select(Concepts)
                                           .filter(Concepts.id != source.id)
                                           .order_by(Concepts.embedding.cosine_distance(source.embedding))
                                           .limit(limit))
        elif operation == 'max_inner_product':
            query_result = session.scalars(select(Concepts)
                                           .filter(Concepts.id != source.id)
                                           .order_by(Concepts.embedding.max_inner_product(source.embedding))
                                           .limit(limit))
        elif operation == 'l1_distance':
            query_result = session.scalars(select(Concepts)
                                           .filter(Concepts.id != source.id)
                                           .order_by(Concepts.embedding.l1_distance(source.embedding))
                                           .limit(limit))
        #elif operation == 'hamming_distance':
        #    query_result = session.scalars(select(Concepts)
        #                                   .filter(Concepts.id != source.id)
        #                                   .order_by(Concepts.embedding.hamming_distance(source.embedding))
        #                                   .limit(limit))
        #elif operation == 'jaccard_distance':
        #    query_result = session.scalars(select(Concepts)
        #                                   .filter(Concepts.id != source.id)
        #                                   .order_by(Concepts.embedding.jaccard_distance(source.embedding))
        #                                   .limit(limit))
        else:
            raise Exception("operation is not supported")
        rtndata = [concept for concept in query_result]
    except Exception as e:
        traceback.print_exc()
    finally:
        session.close()
    
    return rtndata

def update_srctrgnum_tb_concepts_byid() -> Tuple[int, str]:
    """
    keyconcept_list의 source_num, target_num을 갱신한다
    """
    rtncd = 900
    rtnmsg = '실패'
    concept_list = read_tb_networks_all()
    network_list = read_tb_networks_all()

    session = SessionLocal()
    try:
        source_count_dict = {}
        target_count_dict = {}
        for network in network_list:
            source_count_dict[network.source] = source_count_dict.get(network.source, 0) + 1
            target_count_dict[network.target] = target_count_dict.get(network.target, 0) + 1

        print(source_count_dict)
        print(target_count_dict)
        for keyconcept in concept_list:
            session.execute(update(Concepts)
                            .where(Concepts.id == keyconcept.id)
                            .values(source_num = source_count_dict.get(keyconcept.id, 0), 
                                    target_num = target_count_dict.get(keyconcept.id, 0)))
        session.commit()
        rtncd = 200
        rtnmsg = '성공'
    except Exception as e:
        traceback.print_exc()
        session.rollback()
        rtncd = 900
        rtnmsg = '실패'
    finally:
        session.close()

    return rtncd, rtnmsg

"""
Networks 테이블 관련 함수
"""
def create_network_connections_tb_networks(source, target) -> Tuple[bool, str]:
    """
    현재 tb_concepts를 기준으로 네트워크 관계를 tb_networks에 저장한다

    - 임베딩 벡터기준 top_k
    - 임베딩 벡터기준 top_p
      - 상위 p%만큼의 유사도를 가지는 컨셉간 연결
      - 누적 유사도의 비중이 전체 대비 p%가 되는 노드를 선택하여 연결
    """
    rtncd = 900
    rtnmsg = '실패'

    session = SessionLocal()
    try:
        session.execute(insert(Networks), {'source':source, 'target':target})
        session.commit()
        rtncd = 200
        rtnmsg = '성공'
    except Exception as e:
        traceback.print_exc()
        session.rollback()
        rtncd = 900
        rtnmsg = '실패'
    finally:
        session.close()

    return rtncd, rtnmsg

def read_tb_networks_all() -> list[Networks]:
    rtncd = 900
    rtnmsg = '실패'

    session = SessionLocal()
    try:
        query = session.query(Networks)
        rtndata = query.all()
        rtncd = 200
        rtnmsg = '성공'
    except Exception as e:
        traceback.print_exc()
        session.rollback()
        rtncd = 900
        rtnmsg = '실패'
    finally:
        session.close()

    return rtndata

"""
References 테이블 관련 함수
"""
def create_reference_into_tb_references(reference_list: list[dict]) -> Tuple[int, str]:
    rtncd = 900
    rtnmsg = '실패'

    session = SessionLocal()
    try:
        session.execute(insert(References), reference_list)
        session.commit()
        rtncd = 200
        rtnmsg = '성공'
    except Exception as e:
        traceback.print_exc()
        session.rollback()
        rtncd = 900
        rtnmsg = '실패'
    finally:
        session.close()

    return rtncd, rtnmsg

def read_tb_references_all() -> list[References]:
    rtncd = 900
    rtnmsg = '실패'

    session = SessionLocal()
    try:
        query = session.query(References)
        rtndata = query.all()
        rtncd = 200
        rtnmsg = '성공'
    except Exception as e:
        traceback.print_exc()
        session.rollback()
        rtncd = 900
        rtnmsg = '실패'
    finally:
        session.close()

    return rtndata