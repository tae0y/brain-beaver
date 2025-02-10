from typing import Annotated
from fastapi import APIRouter, Depends
from concepts.conceptsservice import ConceptsService
from common.models.responseDTO import ResponseDTO

router = APIRouter(
    prefix="/api/concepts",
)

service = ConceptsService()
def get_service():
    return service

@router.post("")
def create_concepts(
    concepts_list: list[dict],
    service: Annotated[ConceptsService, Depends(get_service)] = get_service
) -> ResponseDTO:
    """
    주요개념을 생성한다.
    """
    return service.create_concepts(concepts_list)

@router.put("/{concept_id}")
def update_concept(
    concepts_list: list[dict]
) -> ResponseDTO:
    """
    주요개념을 갱신한다.
    """
    return service.update_concepts(concepts_list)

@router.put("/{concept_id}/source-target-count")
def update_concept_source_target_count(
    concept_id: int,
    source_num: int,
    target_num: int,
    service: Annotated[ConceptsService, Depends(get_service)] = get_service
) -> ResponseDTO:
    """
    주요개념의 출처와 대상 개수만 갱신한다.
    """
    return service.update_concepts_source_target_count(concept_id, source_num, target_num)

@router.get("")
def get_concepts(
    service: Annotated[ConceptsService, Depends(get_service)] = get_service
) -> ResponseDTO:
    """
    주요개념 목록을 반환한다.
    """
    return service.get_concepts()

@router.get("/{concept_id}")
def get_concept(
    concept_id: int,
    service: Annotated[ConceptsService, Depends(get_service)] = get_service
) -> ResponseDTO:
    """
    주요개념을 반환한다.
    """
    return service.get_concept(concept_id)

@router.get("/count")
def get_concepts_count(
    service: Annotated[ConceptsService, Depends(get_service)] = get_service
) -> ResponseDTO:
    """
    주요개념의 개수를 반환한다.
    """
    return service.get_concepts_count()
