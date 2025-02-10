from pydantic import BaseModel

class ResponseDTO(BaseModel):
    status: str
    message: str
    data: str

    def __str__(self):
        return f"status: {self.status}, message: {self.message}, data: {self.data}"
