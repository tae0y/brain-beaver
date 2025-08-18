import os
import sys

class Constants:
    """
    환경변수를 읽어 상수로 사용하는 싱글톤.
    
    모든 설정값은 환경변수를 통해 주입받습니다.
    개발 시에는 .env 파일을 사용할 수 있습니다.
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

    # RabbitMQ constants
    rabbitmq_user :str
    rabbitmq_passwd :str

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
        환경변수로부터 설정값을 로드합니다.
        개발 시에는 .env 파일이 있다면 자동으로 로드합니다.
        민감한 정보는 기본값을 제공하지 않으며, 비민감한 설정은 적절한 기본값을 제공합니다.
        """
        
        # 개발 편의를 위해 .env 파일이 있다면 로드 (python-dotenv 없이 간단 구현)
        self._load_dotenv_if_exists()
        
        # ---------- Secret Configurations (민감한 설정) ----------
        # DB
        self.db_connection_string = os.getenv('DB_CONNECTION_STRING', '')

        # GooglePSE
        self.google_pse_api_url = os.getenv('GOOGLE_PSE_API_URL', '')
        self.google_pse_api_key = os.getenv('GOOGLE_PSE_API_KEY', '')
        self.google_pse_cx = os.getenv('GOOGLE_PSE_CX', '')
        self.google_pse_datarestict = os.getenv('GOOGLE_PSE_DATARESTRICT', '')
        self.google_pse_filter = os.getenv('GOOGLE_PSE_FILTER', '')
        self.google_pse_h1 = os.getenv('GOOGLE_PSE_H1', '')
        self.google_pse_num = os.getenv('GOOGLE_PSE_NUM', '')
        self.google_pse_safe = os.getenv('GOOGLE_PSE_SAFE', '')

        # NaverAPI
        self.naver_client_id = os.getenv('NAVER_CLIENT_ID', '')
        self.naver_client_secret = os.getenv('NAVER_CLIENT_SECRET', '')
        self.naver_webkr_url = os.getenv('NAVER_WEBKR_URL', 'https://openapi.naver.com/v1/search/webkr.json?query=')

        # OpenAI
        self.openai_api_key = os.getenv('OPENAI_API_KEY', '')

        # RabbitMQ
        self.rabbitmq_user = os.getenv('RABBITMQ_USER', 'admin')
        self.rabbitmq_passwd = os.getenv('RABBITMQ_PASSWD', 'nimda')

        # ---------- Non-Secret Configurations (비민감한 설정) ----------
        # Thread
        self.thread_global_thread_pool = int(os.getenv('THREAD_GLOBAL_THREAD_POOL', '10'))

        # Ollama
        self.ollama_max_queue = int(os.getenv('OLLAMA_MAX_QUEUE', '100'))
        self.ollama_num_parallel = int(os.getenv('OLLAMA_NUM_PARALLEL', '10'))

        # DB
        self.db_echo_truefalse = os.getenv('DB_ECHO_TRUEFALSE', 'False').lower() in ('true', '1', 'yes', 'on')
        self.db_pool_size = int(os.getenv('DB_POOL_SIZE', '50'))
        self.db_max_overflow = int(os.getenv('DB_MAX_OVERFLOW', '0'))

    def _load_dotenv_if_exists(self):
        """
        .env 파일이 존재한다면 환경변수로 로드합니다.
        외부 의존성 없이 간단하게 구현했습니다.
        """
        env_file = '.env'
        if os.path.exists(env_file):
            try:
                with open(env_file, 'r', encoding='utf-8') as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith('#') and '=' in line:
                            key, value = line.split('=', 1)
                            key = key.strip()
                            value = value.strip().strip('"').strip("'")  # Remove quotes
                            # Only set if not already set in environment
                            if key not in os.environ:
                                os.environ[key] = value
            except Exception as e:
                # Silently ignore errors in .env loading
                pass
