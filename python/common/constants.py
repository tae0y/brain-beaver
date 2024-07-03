import os
import sys
import configparser

"""
Singleton class to store all the constants used in the project
constants are read from the ../res/secrets.properties file
"""

class Constants:
    _instance = None

    # Google PSE constants
    google_pse_api_url :str
    google_pse_api_key :str
    google_pse_cx :str
    google_pse_datarestict :str
    google_pse_filter :str
    google_pse_h1 :str
    google_pse_num :str
    google_pse_safe :str

    @staticmethod
    def get_instance():
        if Constants._instance is None:
            Constants()
        return Constants._instance

    def __init__(self):
        if Constants._instance is not None:
            raise Exception("This class is a singleton!")
        else:
            Constants._instance = self
            self.load_constants()

    def load_constants(self):
        config = configparser.ConfigParser()
        config.read('../res/secrets.properties')

        # Google PSE
        self.google_pse_api_url = config.get('Google PSE', 'API_URL')
        self.google_pse_api_key = config.get('Google PSE', 'API_KEY')
        self.google_pse_cx = config.get('Google PSE', 'CX')
        self.google_pse_datarestict = config.get('Google PSE', 'DATARESTRICT')
        self.google_pse_filter = config.get('Google PSE', 'FILTER')
        self.google_pse_h1 = config.get('Google PSE', 'H1')
        self.google_pse_num = config.get('Google PSE', 'NUM')
        self.google_pse_safe = config.get('Google PSE', 'SAFE')

        # Naver API
        self.naver_client_id = config.get('Naver API', 'CLIENT_ID')
        self.naver_client_secret = config.get('Naver API', 'CLIENT_SECRET')
        self.naver_webkr_url = config.get('Naver API', 'WEBKR_URL')