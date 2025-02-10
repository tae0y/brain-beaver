import os
import sys
import configparser

class Constants:
    """
    다음 설정파일을 읽어 상수로 사용하는 싱글톤.

    /properties/config.properties
    /properties/secret.properties
    """
    _instance = None

    # ---------- Secret Configs ---------- 
    # DB
    db_connection_string :str

    # GooglePSE constants
    google_pse_api_url :str
    google_pse_api_key :str
    google_pse_cx :str
    google_pse_datarestict :str
    google_pse_filter :str
    google_pse_h1 :str
    google_pse_num :str
    google_pse_safe :str

    # NaverAPI constants
    naver_client_id :str
    naver_client_secret :str
    naver_webkr_url :str

    # OpenAI constants
    openai_api_key :str

    # ---------- Configs ---------- 
    # Thread constants
    thread_global_thread_pool :int

    # Ollama constants
    ollama_max_queue :int
    ollama_num_parallel :int

    # DB
    db_echo_truefalse :bool
    db_pool_size :int
    db_max_overflow :int


    def __init__(self):
        if Constants._instance is not None:
            raise Exception("This class is a singleton!")
        else:
            Constants._instance = self
            self.load_constants()

    @staticmethod
    def get_instance():
        if Constants._instance is None:
            _instance = Constants()
            _instance.load_constants()
        return Constants._instance

    def load_constants(self):
        """
        secret.properties 파일 로드
        """
        secret = configparser.ConfigParser()
        secret.read('../properties/secret.properties') #app.py가 실행되는 위치 기준으로 설정

        # DB
        self.db_connection_string = secret.get('DB', 'CONNECTION_STRING')

        # GooglePSE
        self.google_pse_api_url = secret.get('GooglePSE', 'API_URL')
        self.google_pse_api_key = secret.get('GooglePSE', 'API_KEY')
        self.google_pse_cx = secret.get('GooglePSE', 'CX')
        self.google_pse_datarestict = secret.get('GooglePSE', 'DATARESTRICT')
        self.google_pse_filter = secret.get('GooglePSE', 'FILTER')
        self.google_pse_h1 = secret.get('GooglePSE', 'H1')
        self.google_pse_num = secret.get('GooglePSE', 'NUM')
        self.google_pse_safe = secret.get('GooglePSE', 'SAFE')

        # NaverAPI
        self.naver_client_id = secret.get('NaverAPI', 'CLIENT_ID')
        self.naver_client_secret = secret.get('NaverAPI', 'CLIENT_SECRET')
        self.naver_webkr_url = secret.get('NaverAPI', 'WEBKR_URL')

        # OpenAI
        self.openai_api_key = secret.get('OpenAI', 'API_KEY')

        """
        config.properties 파일 로드
        """
        config = configparser.ConfigParser()
        config.read('../properties/config.properties') #app.py가 실행되는 위치 기준으로 설정

        # Thread
        self.thread_global_thread_pool = int(config.get('Thread', 'GLOBAL_THREAD_POOL'))

        # Ollama
        self.ollama_max_queue = int(config.get('Ollama', 'MAX_QUEUE'))
        self.ollama_num_parallel = int(config.get('Ollama', 'NUM_PARALLEL'))

        # DB
        self.db_echo_truefalse = config.getboolean('DB', 'ECHO_TRUEFALSE')
        self.db_pool_size = int(config.get('DB', 'POOL_SIZE'))
        self.db_max_overflow = int(config.get('DB', 'MAX_OVERFLOW'))
