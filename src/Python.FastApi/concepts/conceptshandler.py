from typing import Annotated
from fastapi import APIRouter, Depends, Body
from fastapi.responses import JSONResponse
from starlette import status as status
from concepts.conceptsservice import ConceptsService
from concepts.conceptsmodel import Concepts
from common.models.responseDTO import ResponseDTO
import json

router = APIRouter(
    prefix="/api/concepts",
    tags=["Concepts"],
)

service = ConceptsService()
def get_service():
    return service

@router.post(
    "",
    summary="주요개념을 DB에 저장한다",
    description="메시지큐에서 추출된 개념을 받아온다. tb_concepts에 저장한다.",
    responses={
        status.HTTP_200_OK:                    {"description":"데이터 저장 성공", "content":{ "application/json": { "example": { "status": "success", "message": "data created", "data": "..." } } }, "model": ResponseDTO},
        status.HTTP_400_BAD_REQUEST:           {"description":"데이터 저장 실패", "content":{ "application/json": { "example": { "status": "error", "message": "essential input missing", "data": "..." } } }, "model": ResponseDTO},
        status.HTTP_422_UNPROCESSABLE_ENTITY:  {"description":"데이터 저장 실패", "content":{ "application/json": { "example": { "status": "error", "message": "input validation error", "data": "..." } } }, "model": ResponseDTO},
        status.HTTP_500_INTERNAL_SERVER_ERROR: {"description":"데이터 저장 실패", "content":{ "application/json": { "example": { "status": "error", "message": "internal server error", "data": "XXXException occured during ..." } } }, "model": ResponseDTO}
    },
)
def create_concepts(
    concepts_list: Annotated[list[dict], Body(..., examples = [ [{ "title": "개념명", "keywords": "키워드", "category": "카테고리", "summary": "개요", "status": "상태", "data_name": "데이터명", "source_num": 0, "target_num": 0, "create_time": "2021-01-01 00:00:00", "update_time": "2021-01-01 00:00:00", "embedding": [0, 0] }, { "title": "개념명2", "keywords": "키워드2", "category": "카테고리2", "summary": "개요2", "status": "상태2", "data_name": "데이터명2", "source_num": 0, "target_num": 0, "create_time": "2021-01-01 00:00:00", "update_time": "2021-01-01 00:00:00", "embedding": [0, 0] }] ],
    description="concept list" )],
    service: Annotated[ConceptsService, Depends(get_service)] = get_service
) -> ResponseDTO:
    result = service.create_concepts(concepts_list)
    if result['status'] == 'success':
        data = result['data'] #success message string
        content = ResponseDTO( status='success', message='data created', data=data )
        return JSONResponse(status_code=200, content=dict(content))
    else:
        data = result['data'] #error message string
        content = ResponseDTO( status='error', message='internal server error', data=data )
        return JSONResponse(status_code=500, content=dict(content))

@router.put(
    "/{concept_id}",
    summary="주요개념을 DB에서 수정한다",
    description="tb_concepts에서 데이터를 수정한다.",
    responses={
        status.HTTP_200_OK:                    {"description":"데이터 수정 성공", "content":{ "application/json": { "example": { "status": "success", "message": "data updated", "data": "..." } } }, "model": ResponseDTO},
        status.HTTP_400_BAD_REQUEST:           {"description":"데이터 수정 실패", "content":{ "application/json": { "example": { "status": "error", "message": "essential input missing", "data": "..." } } }, "model": ResponseDTO},
        status.HTTP_404_NOT_FOUND:             {"description":"데이터 수정 실패", "content":{ "application/json": { "example": { "status": "error", "message": "data not found", "data": "..." } } }, "model": ResponseDTO},
        status.HTTP_422_UNPROCESSABLE_ENTITY:  {"description":"데이터 수정 실패", "content":{ "application/json": { "example": { "status": "error", "message": "input validation error", "data": "..." } } }, "model": ResponseDTO},
        status.HTTP_500_INTERNAL_SERVER_ERROR: {"description":"데이터 수정 실패", "content":{ "application/json": { "example": { "status": "error", "message": "internal server error", "data": "XXXException occured during ..." } } }, "model": ResponseDTO}
    },
)
def update_concept(
    concepts_list: Annotated[dict, Body(..., examples = [ { "id": 1, "title": "개념명-수정00", "keywords": "키워드-수정00", "category": "카테고리-수정00", "summary": "개요-수정00", "status": "상태-수정00", "data_name": "데이터명-수정00", "source_num": 99, "target_num": 99, "create_time": "2022-01-01 00:00:00", "update_time": "2022-01-01 00:00:00", "embedding": [ 0, 0 ] } ])]
) -> ResponseDTO:
    result = service.update_concepts(concepts_list)
    if result['status'] == 'success':
        data = result['data'] #success message string
        content = ResponseDTO( status='success', message='data updated', data=data )
        return JSONResponse(status_code=200, content=dict(content))
    else:
        data = result['data'] #error message string
        content = ResponseDTO( status='error', message='internal server error', data=data )
        return JSONResponse(status_code=500, content=dict(content))

@router.put(
    "/{concept_id}/source-target-count",
    summary="주요개념의 출처와 대상 개수만 수정한다",
    description="tb_concepts에서 데이터를 수정한다.",
    responses={
        status.HTTP_200_OK:                    {"description":"데이터 수정 성공", "content":{ "application/json": { "example": { "status": "success", "message": "data updated", "data": "..." } } }, "model": ResponseDTO},
        status.HTTP_400_BAD_REQUEST:           {"description":"데이터 수정 실패", "content":{ "application/json": { "example": { "status": "error", "message": "essential input missing", "data": "..." } } }, "model": ResponseDTO},
        status.HTTP_404_NOT_FOUND:             {"description":"데이터 수정 실패", "content":{ "application/json": { "example": { "status": "error", "message": "data not found", "data": "..." } } }, "model": ResponseDTO},
        status.HTTP_422_UNPROCESSABLE_ENTITY:  {"description":"데이터 수정 실패", "content":{ "application/json": { "example": { "status": "error", "message": "input validation error", "data": "..." } } }, "model": ResponseDTO},
        status.HTTP_500_INTERNAL_SERVER_ERROR: {"description":"데이터 수정 실패", "content":{ "application/json": { "example": { "status": "error", "message": "internal server error", "data": "XXXException occured during ..." } } }, "model": ResponseDTO}
    },
    tags=["Concepts"],
)
def update_concept_source_target_count(
    concept_id: int,
    source_num: int,
    target_num: int,
    service: Annotated[ConceptsService, Depends(get_service)] = get_service
) -> ResponseDTO:
    result = service.update_concepts_source_target_count(concept_id, source_num, target_num)
    if result['status'] == 'success':
        data = result['data'] #success message string
        content = ResponseDTO( status='success', message='data updated', data=data )
        return JSONResponse(status_code=200, content=dict(content))
    else:
        data = result['data'] #error message string
        content = ResponseDTO( status='error', message='internal server error', data=data )
        return JSONResponse(status_code=500, content=dict(content))

@router.get(
    "",
    summary="주요개념 전체를 조회한다",
    description="tb_concepts에서 데이터를 조회한다.",
    responses={
        status.HTTP_200_OK:                    {"description":"데이터 조회 성공", "content":{ "application/json": { "example": { "status": "success", "message": "data selected", "data": "..." } } }, "model": ResponseDTO},
        status.HTTP_400_BAD_REQUEST:           {"description":"데이터 조회 실패", "content":{ "application/json": { "example": { "status": "error", "message": "essential input missing", "data": "..." } } }, "model": ResponseDTO},
        status.HTTP_422_UNPROCESSABLE_ENTITY:  {"description":"데이터 조회 실패", "content":{ "application/json": { "example": { "status": "error", "message": "input validation error", "data": "..." } } }, "model": ResponseDTO},
        status.HTTP_500_INTERNAL_SERVER_ERROR: {"description":"데이터 조회 실패", "content":{ "application/json": { "example": { "status": "error", "message": "internal server error", "data": "XXXException occured during ..." } } }, "model": ResponseDTO}
    },
)
def get_concepts(
    service: Annotated[ConceptsService, Depends(get_service)] = get_service
) -> ResponseDTO:
    result = service.get_concepts()
    if result['status'] == 'success':
        data = result['data'] #concepts object list
        data = [o.to_dict() for o in data]
        data = json.loads(json.dumps(data, default=str))
        content = ResponseDTO( status='success', message='data selected', data=data )
        return JSONResponse(status_code=200, content=dict(content))
    else:
        data = result['data'] #error message string
        content = ResponseDTO( status='error', message='internal server error', data=data )
        return JSONResponse(status_code=500, content=dict(content))

@router.get(
    "/{concept_id:int}",
    summary="id를 기준으로 특정 주요개념을 조회한다",
    description="tb_concepts에서 데이터를 조회한다.",
    responses={
        status.HTTP_200_OK:                    {"description":"데이터 조회 성공", "content":{ "application/json": { "example": { "status": "success", "message": "data selected", "data": "..." } } }, "model": ResponseDTO},
        status.HTTP_400_BAD_REQUEST:           {"description":"데이터 조회 실패", "content":{ "application/json": { "example": { "status": "error", "message": "essential input missing", "data": "..." } } }, "model": ResponseDTO},
        status.HTTP_404_NOT_FOUND:             {"description":"데이터 조회 실패", "content":{ "application/json": { "example": { "status": "error", "message": "data not found", "data": "..." } } }, "model": ResponseDTO},
        status.HTTP_422_UNPROCESSABLE_ENTITY:  {"description":"데이터 조회 실패", "content":{ "application/json": { "example": { "status": "error", "message": "input validation error", "data": "..." } } }, "model": ResponseDTO},
        status.HTTP_500_INTERNAL_SERVER_ERROR: {"description":"데이터 조회 실패", "content":{ "application/json": { "example": { "status": "error", "message": "internal server error", "data": "XXXException occured during ..." } } }, "model": ResponseDTO}
    },
)
def get_concept(
    concept_id: int,
    service: Annotated[ConceptsService, Depends(get_service)] = get_service
) -> ResponseDTO:
    result = service.get_concept(concept_id)
    if result['status'] == 'success':
        data = result['data'] #concepts object
        data = data.to_dict()
        data = json.loads(json.dumps(data, default=str))
        content = ResponseDTO( status='success', message='data selected', data=data )
        return JSONResponse(status_code=200, content=dict(content))
    else:
        data = result['data'] #error message string
        content = ResponseDTO( status='error', message='internal server error', data=data )
        return JSONResponse(status_code=500, content=dict(content))

@router.get(
    "/count",
    summary="주요개념의 개수를 조회한다",
    description="tb_concepts에서 데이터를 조회한다.",
    responses={
        status.HTTP_200_OK:                    {"description":"데이터 조회 성공", "content":{ "application/json": { "example": { "status": "success", "message": "data selected", "data": "..." } } }, "model": ResponseDTO},
        status.HTTP_400_BAD_REQUEST:           {"description":"데이터 조회 실패", "content":{ "application/json": { "example": { "status": "error", "message": "essential input missing", "data": "..." } } }, "model": ResponseDTO},
        status.HTTP_422_UNPROCESSABLE_ENTITY:  {"description":"데이터 조회 실패", "content":{ "application/json": { "example": { "status": "error", "message": "input validation error", "data": "..." } } }, "model": ResponseDTO},
        status.HTTP_500_INTERNAL_SERVER_ERROR: {"description":"데이터 조회 실패", "content":{ "application/json": { "example": { "status": "error", "message": "internal server error", "data": "XXXException occured during ..." } } }, "model": ResponseDTO}
    },
)
def get_concepts_count(
    service: Annotated[ConceptsService, Depends(get_service)] = get_service
) -> ResponseDTO:
    result = service.get_concepts_count()
    if result['status'] == 'success':
        data = result['data'] #concepts count integer
        content = ResponseDTO( status='success', message='data selected', data=str(data) )
        return JSONResponse(status_code=200, content=dict(content))
    else:
        data = result['data'] #error message string
        content = ResponseDTO( status='error', message='internal server error', data=data )
        return JSONResponse(status_code=500, content=dict(content))

@router.delete(
    "",
    summary="주요개념 전체를 삭제한다",
    description="tb_concepts에서 데이터를 삭제한다.",
    responses={
        status.HTTP_200_OK:                    {"description":"데이터 삭제 성공", "content":{ "application/json": { "example": { "status": "success", "message": "data deleted", "data": "..." } } }, "model": ResponseDTO},
        status.HTTP_400_BAD_REQUEST:           {"description":"데이터 삭제 실패", "content":{ "application/json": { "example": { "status": "error", "message": "essential input missing", "data": "..." } } }, "model": ResponseDTO},
        status.HTTP_500_INTERNAL_SERVER_ERROR: {"description":"데이터 삭제 실패", "content":{ "application/json": { "example": { "status": "error", "message": "internal server error", "data": "XXXException occured during ..." } } }, "model": ResponseDTO}
    },
)
def delete_concepts_all(
    service: Annotated[ConceptsService, Depends(get_service)] = get_service
) -> ResponseDTO:
    result = service.delete_concepts_all()
    if result['status'] == 'success':
        data = result['data']
        content = ResponseDTO( status='success', message='data deleted', data=data )
        return JSONResponse(status_code=200, content=dict(content))
    else:
        data = result['data']
        content = ResponseDTO( status='error', message='internal server error', data=data )
        return JSONResponse(status_code=500, content=dict(content))