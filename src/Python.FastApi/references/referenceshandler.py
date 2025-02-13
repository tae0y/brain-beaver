from typing import Annotated
from starlette import status as status
from fastapi import APIRouter, Depends, Body
from fastapi.responses import JSONResponse
from references.referencesservice import ReferencesService
from common.models.responseDTO import ResponseDTO

router = APIRouter(
    prefix="/api/references",
    tags=["References"],
)

service = ReferencesService()
def get_service():
    return service

@router.delete(
    "",
    summary="레퍼런스 전체를 삭제한다.",
    description="레퍼런스 테이블을 모두 삭제한다.",
    responses={
        status.HTTP_200_OK:                     {"description":"레퍼런스 테이블 초기화 성공", "content":{ "application/json": { "example": { "status": "success", "message": "data extracted", "data": "..." } } }, "model": ResponseDTO},
        status.HTTP_400_BAD_REQUEST:            {"description":"레퍼런스 테이블 초기화 실패", "content":{ "application/json": { "example": { "status": "error", "message": "essential input missing", "data": "options" } } }, "model": ResponseDTO},
        status.HTTP_500_INTERNAL_SERVER_ERROR:  {"description":"레퍼런스 테이블 초기화 실패", "content":{ "application/json": { "example": { "status": "error", "message": "internal server error", "data": "XXXException occured during ..." } } }, "model": ResponseDTO}
    },
)
def delete_refereces_all(
    service: Annotated[ReferencesService, Depends(get_service)] = get_service,
) -> ResponseDTO:
    """
    expand_keyconcpts 테이블을 초기화한다.
    """
    status = 0
    content = None
    try:
        service.delete_refereces_all()
        status = 200
        content = ResponseDTO( status='success', message='data deleted', data='' )
    except Exception as e:
        status = 500
        content = ResponseDTO( status='error', message='internal server error', data=str(e) )

    return JSONResponse(status_code=status, content=dict(content))

@router.post(
    "/expand",
    summary="주요개념 확장을 위해 웹검색을 수행하고 저장한다.",
    description="주요개념 확장을 위해 웹검색을 수행하고 저장한다.",
    responses={
        status.HTTP_200_OK:                     {"description":"웹검색 성공", "content":{ "application/json": { "example": { "status": "success", "message": "data extracted", "data": "..." } } }, "model": ResponseDTO},
        status.HTTP_400_BAD_REQUEST:            {"description":"웹검색 실패", "content":{ "application/json": { "example": { "status": "error", "message": "essential input missing", "data": "options" } } }, "model": ResponseDTO},
        status.HTTP_500_INTERNAL_SERVER_ERROR:  {"description":"웹검색 실패", "content":{ "application/json": { "example": { "status": "error", "message": "internal server error", "data": "XXXException occured during ..." } } }, "model": ResponseDTO}
    },
)
def expand_keyconcepts_with_websearch(
    options: Annotated[dict, Body(..., examples=[ 
        { "action_type": "top", "action_limit": 10, "reason_model_name": "gemma2:9b-instruct-q5_K_M", "quorum_check" : "true" }, 
        { "action_type": "all" } ])],
    service: Annotated[ReferencesService, Depends(get_service)] = get_service,
) -> ResponseDTO:
    """
    주요개념 확장을 위해 웹검색을 수행하고 저장한다.
    """
    status = 0
    content = None
    try:
        service.expand_keyconcepts_with_websearch(options)
        status = 200
        content = ResponseDTO( status='success', message='data extracted', data='' )
    except Exception as e:
        status = 500
        content = ResponseDTO( status='error', message='internal server error', data=str(e) )

    return JSONResponse(status_code=status, content=dict(content))

@router.get(
    "",
    summary="레퍼런스 전체를 조회한다.",
    description="레퍼런스 테이블 전체를 조회한다.",
    responses={
        status.HTTP_200_OK:                     {"description":"레퍼런스 조회 성공", "content":{ "application/json": { "example": { "status": "success", "message": "data extracted", "data": "..." } } }, "model": ResponseDTO},
        status.HTTP_500_INTERNAL_SERVER_ERROR:  {"description":"레퍼런스 조회 실패", "content":{ "application/json": { "example": { "status": "error", "message": "internal server error", "data": "XXXException occured during ..." } } }, "model": ResponseDTO}
    },
)
def get_references(
    service: Annotated[ReferencesService, Depends(get_service)] = get_service,
) -> ResponseDTO:
    """
    레퍼런스 테이블을 조회한다.
    """
    status = 0
    content = None
    try:
        result = service.read_references_all()
        status = 200
        content = ResponseDTO( status='success', message='data extracted', data=str(result) )
    except Exception as e:
        status = 500
        content = ResponseDTO( status='error', message='internal server error', data=str(e) )

    return JSONResponse(status_code=status, content=dict(content))
