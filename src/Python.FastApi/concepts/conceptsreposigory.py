from typing import Tuple
import traceback
from sqlalchemy import insert, select, update, desc
from common.db.db import DB
from concepts.conceptsmodel import Concepts

class ConceptsRepository():
    """
    tb_concepts 테이블 관련 함수
    """
    def __init__(self):
        self.db = DB.get_instance()
        pass

    def create_tb_concepts_list(self, keyconcept_list: list[dict]) -> Tuple[int, str]:
        """
        tb_concepts 테이블에 딕셔너리 리스트를 입력받아 모두 저장한다
        """
        rtncd = 900
        rtnmsg = '실패'

        session = self.db.get_session(write=True)
        try:
            session.execute(insert(Concepts), keyconcept_list)
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

    def read_tb_concepts_all(self) -> list[Concepts]:
        """
        tb_concepts 테이블의 모든 데이터를 읽어온다
        """
        session = self.db.get_session(write=False)
        try:
            query = session.query(Concepts)
            rtndata = query.all()
        except Exception as e:
            traceback.print_exc()
            rtndata = []
        finally:
            session.close()
        return rtndata

    def read_tb_concepts_by_id(self, concpet_id : str) -> Concepts:
        """
        tb_concepts 테이블에서 concpet_id로 데이터를 읽어온다
        """
        session = self.db.get_session(write=False)
        try:
            query = session.query(Concepts).filter(Concepts.id == concpet_id)
            rtndata = query.first()
        except Exception as e:
            traceback.print_exc()
        finally:
            session.close()
        return rtndata

    def read_tb_concepts_count(self) -> int:
        """
        tb_concepts 테이블의 데이터 수를 읽어온다
        """
        session = self.db.get_session(write=False)
        try:
            query = session.query(Concepts)
            rtndata = query.count()
        except Exception as e:
            traceback.print_exc()
            rtndata = 0
        finally:
            session.close()
        return rtndata

    def read_tb_concepts_top_by_source_target_num(self, limit: int) -> list[Concepts]:
        """
        tb_concepts 테이블에서 상위 limit개의 데이터를 읽어온다
        """
        session = self.db.get_session(write=False)
        try:
            query = session.query(Concepts).order_by(desc(Concepts.source_num+Concepts.target_num)).limit(limit)
            rtndata = query.all()
        except Exception as e:
            traceback.print_exc()
            rtndata = []
        finally:
            session.close()
        return rtndata

    def read_tb_concepts_by_id(self, concept_id : int) -> Concepts:
        """
        tb_concepts 테이블에서 concept_id로 데이터를 읽어온다
        """
        session = self.db.get_session(write=False)
        try:
            query = session.query(Concepts).filter(Concepts.id == concept_id)
            rtndata = query.first()
        except Exception as e:
            traceback.print_exc()
        finally:
            session.close()
        return rtndata


    def read_tb_concepts_nearest_by_embedding(self, source : Concepts, operation: str, limit: int) -> list[Concepts]:
        """
        tb_concepts 테이블에서 source와 가장 가까운 개념을 operation에 따라 limit개수만큼 읽어온다
        """
        session = self.db.get_session(write=False)
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


    def update_tb_concepts(self, concepts: dict) -> Tuple[int, str]:
        """
        tb_concepts 테이블의 데이터를 갱신한다
        """
        rtncd = 900
        rtnmsg = '실패'
        session = self.db.get_session(write=True)
        try:
            session.execute(update(Concepts)
                            .where(Concepts.id == concepts['id'])
                            .values(
                                title = concepts['title'],
                                keywords = concepts['keywords'],
                                category = concepts['category'],
                                summary = concepts['summary'],
                                status = concepts['status'],
                                data_name = concepts['data_name'],
                                source_num = concepts['source_num'],
                                target_num = concepts['target_num'],
                                create_time = concepts['create_time'],
                                update_time = concepts['update_time'],
                                embedding = concepts['embedding']
                            )
            )
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



    def update_tb_concepts_source_target_count(self, concept_id, source_num, target_num) -> Tuple[int, str]:
        """
        keyconcept_list의 source_num, target_num을 갱신한다
        """
        rtncd = 900
        rtnmsg = '실패'
        session = self.db.get_session(write=True)
        try:
            session.execute(update(Concepts)
                            .where(Concepts.id == concept_id)
                            .values(source_num = source_num,
                                    target_num = target_num)
            )
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


    def read_tb_concepts_all_idonly(self) -> list[int]:
        """
        tb_concepts 테이블의 모든 id를 읽어온다
        """
        session = self.db.get_session(write=False)
        try:
            query = session.query(Concepts.id)
            rtndata = query.all()
        except Exception as e:
            traceback.print_exc()
            rtndata = []
        finally:
            session.close()
        return rtndata

    def delete_tb_concepts_all(self) -> list[int]:
        """
        tb_concepts 테이블의 모든 데이터를 삭제한다
        """
        rtncd = 900
        rtnmsg = '실패'
        session = self.db.get_session(write=True)
        try:
            session.query(Concepts).delete()
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