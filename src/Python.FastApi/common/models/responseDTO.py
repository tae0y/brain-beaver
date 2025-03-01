from typing import Any
from pydantic import BaseModel

class ResponseDTO(BaseModel):
    status: str
    message: str
    data: Any

    def __dict__(self):
        return {
            "status": self.status,
            "message": self.message,
            "data": self.data
        }

    def __str__(self):
        return self.__dict__()

    def __repr__(self):
        return self.__dict__()
