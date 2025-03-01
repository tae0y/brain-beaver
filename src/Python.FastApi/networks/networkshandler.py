from typing import Annotated
from fastapi import APIRouter, Depends, Body
from fastapi.responses import JSONResponse
from starlette import status as status
from networks.networksservice import NetworksService
from common.models.responseDTO import ResponseDTO
import json

router = APIRouter(
    prefix="/api/networks",
    tags=["Networks"],
)

service = NetworksService()
def get_service():
    return service

@router.post(
    "/engage",
    summary="주요개념을 네트워크로 연결한다.",
    description="임베딩 벡터 유사도를 기준으로 관련개념을 연결한다.",
    responses={
        status.HTTP_200_OK:                     {"description":"네트워크 연결 성공", "content":{ "application/json": { "example": { "status": "success", "message": "data extracted", "data": "..." } } }, "model": ResponseDTO},
        status.HTTP_400_BAD_REQUEST:            {"description":"네트워크 연결 실패", "content":{ "application/json": { "example": { "status": "error", "message": "essential input missing", "data": "options" } } }, "model": ResponseDTO},
        status.HTTP_422_UNPROCESSABLE_ENTITY:   {"description":"네트워크 연결 실패", "content":{ "application/json": { "example": { "status": "error", "message": "input validation error", "data": "..." } } }, "model": ResponseDTO},
        status.HTTP_500_INTERNAL_SERVER_ERROR:  {"description":"네트워크 연결 실패", "content":{ "application/json": { "example": { "status": "error", "message": "internal server error", "data": "XXXException occured during ..." } } }, "model": ResponseDTO}
    },
)
def engage_keyconcepts_into_networks(
    options: Annotated[dict, Body(..., examples=[ { "operation": "cosine_distance", "cosine_sim_check" : "true" } ])],
    service: Annotated[NetworksService, Depends(get_service)] = get_service,
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
    status = 0
    content = None
    try:
        service.engage_keyconcepts_into_networks(options)
        status = 200
        content = ResponseDTO( status='success', message='data extracted', data='' )
    except Exception as e:
        status = 500
        content = ResponseDTO( status='error', message='internal server error', data=str(e) )

    return JSONResponse(status_code=status, content=dict(content))

@router.get(
    "",
    summary="네트워크 전체를 조회한다.",
    description="네트워크 테이블 전체를 조회한다.",
    responses={
        status.HTTP_200_OK:                     {"description":"네트워크 조회 성공", "content":{ "application/json": { "example": { "status": "success", "message": "data extracted", "data": "..." } } }, "model": ResponseDTO},
        status.HTTP_500_INTERNAL_SERVER_ERROR:  {"description":"네트워크 조회 실패", "content":{ "application/json": { "example": { "status": "error", "message": "internal server error", "data": "XXXException occured during ..." } } }, "model": ResponseDTO}
    },
)
def get_networks(
    service: Annotated[NetworksService, Depends(get_service)] = get_service,
) -> ResponseDTO:
    """
    네트워크를 조회한다.
    """
    status = 0
    content = None
    try:
        result = service.read_networks_all()
        result = [o.to_dict() for o in result]
        result = json.loads(json.dumps(result, default=str))
        status = 200
        content = ResponseDTO( status='success', message='data extracted', data=result )
    except Exception as e:
        status = 500
        content = ResponseDTO( status='error', message='internal server error', data=str(e) )

    return JSONResponse(status_code=status, content=dict(content))

@router.delete(
    "",
    summary="네트워크 전체를 삭제한다.",
    description="네트워크 테이블 전체를 삭제한다.",
    responses={
        status.HTTP_200_OK:                     {"description":"네트워크 삭제 성공", "content":{ "application/json": { "example": { "status": "success", "message": "data deleted", "data": "" } } }, "model": ResponseDTO},
        status.HTTP_500_INTERNAL_SERVER_ERROR:  {"description":"네트워크 삭제 실패", "content":{ "application/json": { "example": { "status": "error", "message": "internal server error", "data": "XXXException occured during ..." } } }, "model": ResponseDTO}
    },
)
def delete_networks_all(
    service: Annotated[NetworksService, Depends(get_service)] = get_service,
) -> ResponseDTO:
    """
    네트워크 테이블 전체를 삭제한다.
    """
    status = 0
    content = None
    try:
        service.delete_networks_all()
        status = 200
        content = ResponseDTO( status='success', message='data deleted', data='' )
    except Exception as e:
        status = 500
        content = ResponseDTO( status='error', message='internal server error', data=str(e) )

    return JSONResponse(status_code=status, content=dict(content)
)