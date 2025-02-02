from typing import Tuple
import traceback
from sqlalchemy import insert, select
from common.db.db import DB
from expand.references.referencesmodel import References

class ReferencesRepository():
    """
    tb_references 테이블 관련 함수
    """
    def __init__(self):
        self.db = DB.get_instance()
        pass

    def create_reference_into_tb_references(self, reference_list: list[dict]) -> Tuple[int, str]:
        rtncd = 900
        rtnmsg = '실패'

        session = self.db.get_session()
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

    def read_tb_references_all(self) -> list[References]:
        rtncd = 900
        rtnmsg = '실패'

        session = self.db.get_session()
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