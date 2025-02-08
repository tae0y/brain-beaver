from abc import ABC, abstractmethod
from engage.llmroute.responseDTO import ResponseDTO

class BaseClient(ABC):
    """
    공통 LLM API 클라이언트 인터페이스
    """
    @abstractmethod
    def generate(self, prompt: str, options: dict) -> ResponseDTO:
        pass

    @abstractmethod
    def embed(self, input: str, options: dict, operation: str) -> ResponseDTO:
        pass

    @abstractmethod
    def get_how_much_cost(self, text) -> float:
        pass

    @abstractmethod
    def get_token_count(self, text) -> int:
        pass

    @abstractmethod
    def get_cost_per_token(self) -> float:
        pass

    @abstractmethod
    def get_chunk_size(self) -> int:
        pass