from expand.references.referencesservice import ReferencesService

class ReferencesHandler:
    """
    references 관련 요청을 처리한다.
    """
    def __init__(self):
        self.service = ReferencesService()
        # ...existing code...

    def perform_search(self, query: str, options: dict = None):
        # ...existing code...
        return self.service.execute_search(query, options)
