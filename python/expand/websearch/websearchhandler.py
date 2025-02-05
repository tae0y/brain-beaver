from expand.websearch.websearchservice import WebSearchService

class WebSearchHandler:
    """
    웹검색 관련 요청을 처리한다.
    """
    def __init__(self):
        self.service = WebSearchService()
        # ...existing code...

    def perform_search(self, query: str, options: dict = None):
        # ...existing code...
        return self.service.execute_search(query, options)
