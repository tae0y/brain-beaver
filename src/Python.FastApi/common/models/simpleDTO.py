class SimpleDTO():
    status: str
    message: str
    data: str

    def __init__(self, status: str, message: str, data: str):
        self.status = status
        self.message = message
        self.data = data

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
