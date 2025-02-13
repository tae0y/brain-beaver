from ..system.constants import Constants

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

class DB():
    """
    sqlalchemy DB 세션을 관리하는 클래스
    """
    _instance = None

    def __init__(self):
        if DB._instance is not None:
            raise Exception("This class is a singleton!")
        else:
            DB._instance = self
            self.load_db()
        pass


    @staticmethod
    def get_instance():
        if DB._instance is None:
            _instance = DB()
            _instance.load_db()
        return DB._instance


    def get_session(self):
        """
        DB 세션 생성자로 세션을 반환.
        """
        return self.sessionmaker()


    def load_db(self):
        """
        설정파일에 맞춰 DB 세션 생성자를 만든다.
        """
        constants = Constants.get_instance()

        engine = create_engine(
            url = constants.db_connection_string,
            echo = constants.db_echo_truefalse,
            pool_size = constants.db_pool_size,
            max_overflow = constants.db_max_overflow
        )
        self.sessionmaker = sessionmaker(
            autocommit=False, 
            autoflush=False, 
            bind=engine
        )
        print("LOG-DEBUG: DB session created. (load_db)")

        pass