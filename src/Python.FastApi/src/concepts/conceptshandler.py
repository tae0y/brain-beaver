from typing import Annotated
from fastapi import APIRouter
from concepts.conceptsservice import ConceptsService
from common.models.responseDTO import ResponseDTO

router = APIRouter(
    prefix="/api/concepts",
)

class ConceptsHandler:
    """
    주요개념 추출과 관련된 요청을 처리한다.
    """

    service : ConceptsService

    def __init__(self):
        self.service = ConceptsService()
        pass

    @router.post("")
    def create_concepts(
        self,
        concepts_list: list[dict]
    ) -> ResponseDTO:
        """
        주요개념을 생성한다.
        """
        return self.service.create_concepts(concepts_list)

    @router.put("/{concept_id}")
    def update_concept(
        self,
        concepts_list: list[dict]
    ) -> ResponseDTO:
        """
        주요개념을 갱신한다.
        """
        return self.service.update_concepts(concepts_list)

    @router.get("")
    def get_concepts(
        self
    ) -> ResponseDTO:
        """
        주요개념 목록을 반환한다.
        """
        return self.service.get_concepts()

    @router.get("/{concept_id}")
    def get_concept(
        self,
        concept_id: int
    ) -> ResponseDTO:
        """
        주요개념을 반환한다.
        """
        return self.service.get_concept(concept_id)

    @router.get("/count")
    def get_concepts_count(
        self
    ) -> ResponseDTO:
        """
        주요개념의 개수를 반환한다.
        """
        return self.service.get_concepts_count()
