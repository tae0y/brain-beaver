import os
import sys
import configparser

"""
Singleton class to store all the constants used in the project
constants are read from the ../res/secrets.properties file
"""

class Constants:
    _instance = None

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

    # Ollama constants
    #ollama_file_thread_count :int
    #ollama_chunk_thread_count :int
    ollama_global_thread_pool = None

    @staticmethod
    def get_instance():
        if Constants._instance is None:
            _instance = Constants()
            _instance.load_constants()
        return Constants._instance

    def __init__(self):
        if Constants._instance is not None:
            raise Exception("This class is a singleton!")
        else:
            Constants._instance = self
            self.load_constants()

    def load_constants(self):
        """
        Load constants from ../res/secrets.properties file
        """
        secret = configparser.ConfigParser()
        secret.read('./res/secret.properties') #app.py가 실행되는 위치 기준으로 설정

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

        """
        Load constants from ../res/config.properties file
        """
        config = configparser.ConfigParser()
        config.read('./res/config.properties') #app.py가 실행되는 위치 기준으로 설정

        #self.ollama_thread_count = int(config.get('Ollama', 'FILE_THREAD_COUNT'))
        #self.ollama_looped_thread_count = int(config.get('Ollama', 'CHUNK_THREAD_COUNT'))
        self.ollama_global_thread_pool = int(config.get('Ollama', 'GLOBAL_THREAD_POOL'))
