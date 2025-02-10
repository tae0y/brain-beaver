from fastapi import APIRouter
from networks.networksservice import NetworksService
from common.models.responseDTO import ResponseDTO

router = APIRouter(
    prefix="/api/networks",
)

class NetworksHandler:
    """
    주요개념 추출과 관련된 요청을 처리한다.

    """

    service : NetworksService

    def __init__(self):
        self.service = NetworksService()
        pass

    @router.post("/engage_keyconcepts_into_networks")
    def engage_keyconcepts_into_networks(
        self, 
        options: dict
    ) -> ResponseDTO:
        """
        주요개념을 네트워크로 연결한다

        TODO 2 : 코사인유사도 임계값 조정, 유사도 비교하는 로직 변경 등으로 지식간 '연관관계'를 잘 표현할 수 있도록 개선

        - options
            - operation : str
                - 'cosine_distance' : 코사인 거리를 이용한 유사도 측정
                - 'max_inner_product' : 내적을 이용한 유사도 측정
                - 'l1_distance' : L1 거리를 이용한 유사도 측정
        """
        self.service.engage_keyconcepts_into_networks(options)
        pass