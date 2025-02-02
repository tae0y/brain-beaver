from engage.networks.networksservice import NetworksService

class NetworksHandler:
    """
    주요개념 추출과 관련된 요청을 처리한다.
    """
    # TODO: Controller, Service 레이어 분리

    service : NetworksService

    def __init__(self):
        self.service = NetworksService()
        pass

    def engage_keyconcepts_into_networks(self, options: dict):
        """
        주요개념을 네트워크로 연결한다

        - options
            - operation : str
                - 'cosine_distance' : 코사인 거리를 이용한 유사도 측정
                - 'max_inner_product' : 내적을 이용한 유사도 측정
                - 'l1_distance' : L1 거리를 이용한 유사도 측정
        """
        self.service.engage_keyconcepts_into_networks(options)
        pass