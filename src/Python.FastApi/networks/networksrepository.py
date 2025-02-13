from typing import Tuple
import traceback
from sqlalchemy import insert, select
from common.db.db import DB
from networks.networksmodel import Networks

class NetworksRepository():
    """
    tb_networks 테이블 관련 함수
    """
    def __init__(self):
        self.db = DB.get_instance()
        pass

    def create_network_connections_tb_networks(self, source, target) -> Tuple[bool, str]:
        """
        현재 tb_concepts를 기준으로 네트워크 관계를 tb_networks에 저장한다

        - 임베딩 벡터기준 top_k
        - 임베딩 벡터기준 top_p
          - 상위 p%만큼의 유사도를 가지는 컨셉간 연결
          - 누적 유사도의 비중이 전체 대비 p%가 되는 노드를 선택하여 연결
        """
        rtncd = 900
        rtnmsg = '실패'

        session = self.db.get_session()
        try:
            session.execute(insert(Networks), {'source_concept_id':source, 'target_concept_id':target})
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

    def read_tb_networks_all(self) -> list[Networks]:
        rtncd = 900
        rtnmsg = '실패'

        session = self.db.get_session()
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

    def delete_tb_networks_all(self) -> Tuple[bool, str]:
        rtncd = 900
        rtnmsg = '실패'

        session = self.db.get_session()
        try:
            session.query(Networks).delete()
            session.commit()
            rtncd = 200
            rtnmsg = '성공'
        except Exception as e:
            traceback.print_exc()
            session.rollback()
            rtncd = 900
            rtnmsg = '실패'

        return rtncd, rtnmsg