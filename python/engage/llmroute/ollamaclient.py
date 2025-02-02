from engage.llmroute.baseclient import BaseClient
from engage.llmroute.responseDTO import ResponseDTO
import ollama
from transformers import AutoTokenizer
import json

class OllamaClient(BaseClient):
    """
    Ollama 모델 API 클라이언트
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
    토큰당 비용
    '''
    cost_per_token: float

    def __init__(self, model_name: str, options: dict):
        model_details = ollama.show(model_name).modelinfo
        architecture = model_details['general.architecture']
        chunk_size = options['chunk_size'] if 'chunk_size' in options else 2048
        cost_per_token = options['cost_per_token'] if 'cost_per_token' in options else 0.000

        self.model_name = model_name
        self.mode_architecture = architecture

        self.context_length = model_details[architecture+'.context_length']
        self.chunk_size = min(self.context_length, chunk_size)
        self.embedding_length = model_details[architecture+'.embedding_length']

        self.tokenizer_type = model_details['tokenizer.ggml.model']
        #self.tokenizer_callable = self.load_tokenizer()
        self.cost_per_token = cost_per_token


    def generate(self, prompt: str, options: dict) -> ResponseDTO:
        """
        프롬프트 입력을 받아 텍스트 생성 결과 반환
        - param
            prompt : str : 프롬프트 텍스트
            options : dict : 옵션
        - return
            ResponseDTO : 응답 객체
            - data: json : 생성 결과 (options['format']에 따라 다름)
        """
        try:
            # refer to https://github.com/ollama/ollama/blob/main/docs/api.md#request-structured-outputs
            default_format = {
                "type" : "object",
                "properties" : {
                    "text" : {
                        "type" : "string"
                    }
                },
                "required" : ["text"]
            }
            response = ollama.generate(
                    model = self.model_name, 
                    prompt = prompt, 
                    format = options['format'] if 'format' in options else default_format,
                    stream = False,
                    options = {k: v for k, v in options.items() if k != 'format'}
                )

            return ResponseDTO(100, 'Success', json.loads(response.response))
        except Exception as e:
            return ResponseDTO(900, f"Internal Server Error - {str(e)}", None)

    def embed(self, input, options: dict, operation: str) -> ResponseDTO:
        """
        텍스트 입력을 받아 임베딩 결과 반환
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
        try:
            response = ollama.embed(
                    model = self.model_name, 
                    input = input, 
                    options = options
                )

            if (operation is not None) and (operation == 'batch'):
                return ResponseDTO(100, 'Success', response.embeddings)
            else:
                return ResponseDTO(100, 'Success', response.embeddings[0])
        except Exception as e:
            return ResponseDTO(900, f"Internal Server Error - {str(e)}", None)


    def load_tokenizer(self):
        """
        토크나이저 로드
        """
        #if "qwen" in [self.mode_architecture, self.tokenizer_type, self.model_name]:
        #    self.tokenizer_callable = AutoTokenizer.from_pretrained("Qwen/Qwen-7B")
        #elif "llama" in [self.mode_architecture, self.tokenizer_type, self.model_name]:
        #    self.tokenizer_callable = AutoTokenizer.from_pretrained("meta-llama/Llama-2-7b-hf")
        #elif "mistral" in [self.mode_architecture, self.tokenizer_type, self.model_name]:
        #    self.tokenizer_callable = AutoTokenizer.from_pretrained("mistralai/Mistral-7B-v0.1")
        #elif "gemma" in [self.mode_architecture, self.tokenizer_type, self.model_name]:
        #    self.tokenizer_callable = AutoTokenizer.from_pretrained("google/gemma-7B")
        #else:
        #    print(f"LOG-ERROR Error during tokenizer loading. cannot find proper tokenizer")
        pass

    def get_how_much_cost(self, text) -> float:
        #return self.get_token_count(text) * self.cost_per_token()
        print("LOG-DEBUG : Ollama is free!! Fell free to use it.")
        return 0.0

    def get_token_count(self, text) -> int:
        if self.tokenizer_callable is None:
            raise Exception("Tokenizer is not loaded")
        else:
            return len(self.tokenizer_callable.tokenize(text))

    def get_cost_per_token(self) -> float:
        return self.cost_per_token

    def get_chunk_size(self) -> int:
        return self.chunk_size