import tiktoken
import datetime
from pydantic import BaseModel
from openai import OpenAI
import FinanceDataReader as fdr
import numpy as np
from engage.llmroute.baseclient import BaseClient
from engage.llmroute.responseDTO import ResponseDTO
import json

class OpenAIClient(BaseClient):
    """
    OpenAI 모델 API 클라이언트
    """

    '''
    모델 이름
    '''
    model_name: str

    '''
    모델 아키텍처
    '''
    mode_architecture: str

    '''
    컨텍스트 길이
    '''
    context_length: int

    '''
    청크 사이즈
    '''
    chunk_size: int

    '''
    임베딩 차원 수
    '''
    embedding_length: int

    '''
    토크나이저 종류
    '''
    tokenizer_type: str

    '''
    토크나이저 함수 호출자
    '''
    tokenizer_callable: callable

    '''
    토큰당 비용 (달러)
    '''
    cost_per_token: float

    '''
    클라이언트
    '''
    client: OpenAI

    '''
    원/달러 환율
    '''
    currency_rates: float


    def __init__(self, model_name: str, options: dict):
        self.client = OpenAI(
            api_key = options['api_key'] if 'api_key' in options else None,
        )

        self.model_name = model_name
        self.mode_architecture = 'GPT'

        self.context_length = options['context_length'] if 'context_length' in options else 2048
        self.chunk_size = min(self.context_length, options['chunk_size'] if 'chunk_size' in options else 2048)
        self.embedding_length = options['embedding_length'] if 'embedding_length' in options else 2048

        self.tokenizer_type = None
        #self.tokenizer_callable = self.load_tokenizer()
        self.cost_per_token = options['cost_per_token'] if 'cost_per_token' in options else float('inf')

        # 환율 계산
        try:
            df = fdr.DataReader('USD/KRW')[-7:] # 최근 7일 환율
            today = datetime.datetime.today().strftime('%Y-%m-%d')
            if today in df.index: # 오늘 최고가
                today_row = df.loc[today]
                self.currency_rates = float(today_row['Close'] if np.isnan(today_row['Close']) else today_row['High'])
            else: # 전날 종가
                self.currency_rates = float(df.iloc[-1]['Close'])
        except:
            self.currency_rates = 1500.0
            print("LOG-ERROR: 환율 조회 실패, 1500원으로 가정합니다!!")


    def generate(self, prompt: str, options: dict) -> ResponseDTO:
        """
        프롬프트 입력을 받아 텍스트 생성 결과 반환
        - 지원모델 : gpt-4o-mini($0.15) ~~o1-mini($1.10), o3-mini($1.10), gpt-3.5-turbo($0.50)~~

        - param
            prompt : str : 프롬프트 텍스트
            options : dict : 옵션
        - return
            ResponseDTO : 응답 객체
            - data: json : 생성 결과 (options['format']에 따라 다름)
        """
        if self.model_name not in ["gpt-4o-mini"]:
            raise ValueError(f"지원되지 않는 모델입니다: {self.model_name}")

        try:
            # refer to https://platform.openai.com/docs/guides/text-generation?example=json
            default_format = {
                "type": "json_schema",
                "json_schema": {
                    "name": "response_schema",
                    "schema": {
                        "type": "object",
                        "properties": {
                            "text": {
                                "description": "generated response text",
                                "type": "string"
                            },
                            "additionalProperties": False
                        }
                    }
                }
            }

            # client.completions.create는 response_format을 지원하지 않고, prompt를 인자로 받음
            # client.chat.completions.create는 response_format을 지원하고, messages를 인자로 받음
            response = self.client.chat.completions.create(
                model = self.model_name,
                messages = [
                    {
                        "role" : "user",
                        "content" : prompt
                    },
                ],
                response_format = options['format'] if 'format' in options else default_format
            )
            return ResponseDTO(100, 'Success', json.loads(response.choices[0].message.content))
        except Exception as e:
            return ResponseDTO(900, f"Internal Server Error - {str(e)}", None)



    def embed(self, input: str, options: dict, operation: str = None) -> ResponseDTO:
        """
        텍스트 입력을 받아 임베딩 결과 반환
        - 지원모델 : text-embedding-3-small($0.02) 1536차원

        - param
            input : str : 입력 텍스트
            options : dict : 옵션
            type : str : 'batch' or 'single'
        - return
            ResponseDTO : 응답 객체
            - data : 임베딩 결과
              - operation이 batch인 경우 -> list[list[float]]
              - 그외 -> list[float]
        """
        if self.model_name not in ["text-embedding-3-small"]:
            raise ValueError(f"지원되지 않는 모델입니다: {self.model_name}")

        try:
            response = self.client.embeddings.create(
                model = self.model_name,
                input = input
            )
            return ResponseDTO(100, 'Success', response.data[0].embedding)

        except Exception as e:
            return ResponseDTO(900, f"Internal Server Error - {str(e)}", None)

    def load_tokenizer(self):
        """
        토크나이저 로드
        """
        model_name = self.model_name.lower()

        if model_name in ["gpt-4o-mini"]:
            #self.tokenizer_callable = tiktoken.get_encoding("o200k_base")
            return tiktoken.get_encoding("o200k_base")
        elif model_name in ["text-embedding-3-small"]:
            #self.tokenizer_callable = tiktoken.get_encoding("cl100k_base")
            return tiktoken.get_encoding("cl100k_base")
        else:
            raise ValueError(f"지원되지 않는 모델입니다: {model_name}")

    def get_how_much_cost(self, text) -> float:
        """
        비용을 원화로 환산하여 반환한다.
        - 모델이름을 기준으로 tiktoken 토크나이저를 로드
        - 토큰당비용은 모델클라이언트 생성시 옵션으로 직접지정
        - 환율은 오늘 최고가 혹은 전날 종가 기준으로 계산
        - 산식 : 토큰수 * 토큰당비용 * 환율 * 2 (input, output)
        """
        return self.get_token_count(text) * self.get_cost_per_token() * self.currency_rates * 2

    def get_token_count(self, text) -> int:
        try:
            return len(self.load_tokenizer().encode(text))
        except:
            print("LOG-ERROR: get_token_count() failed")

    def get_cost_per_token(self) -> float:
        return self.cost_per_token

    def get_chunk_size(self) -> int:
        return self.chunk_size