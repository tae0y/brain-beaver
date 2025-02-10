from typing import Annotated
from fastapi import APIRouter, Body, Depends
from starlette import status as status
from fastapi.responses import JSONResponse
from common.models.responseDTO import ResponseDTO
from extract.extractservice import ExtractService

router = APIRouter(
    prefix="/api/extract",
)

service = ExtractService()
def get_service():
    return service

@router.post(
    "/check-budget",
    summary="데이터에서 주요개념을 추출하는 비용을 추정한다.",
    description="데이터타입에 따라 데이터소스로부터 데이터를 읽어들인다. 데이터 양에 따라 필요한 토큰 값을 추정한다.",
    responses={
        status.HTTP_200_OK:                    {"description":"데이터 추출 성공", "content":{ "application/json": { "example": { "status": "success", "message": "data extracted", "data": { "reasoning_sum": 1000, "embedding_sum": 1000, } } } }, "model": ResponseDTO},
        status.HTTP_400_BAD_REQUEST:           {"description":"데이터 추출 실패", "content":{ "application/json": { "example": { "status": "error", "message": "essential input missing", "data": "datatype" } } }, "model": str},
        status.HTTP_422_UNPROCESSABLE_ENTITY:  {"description":"데이터 추출 실패", "content":{ "application/json": { "example": { "status": "error", "message": "input validation error", "data": "" } } }, "model": str},
        status.HTTP_500_INTERNAL_SERVER_ERROR: {"description":"데이터 추출 실패", "content":{ "application/json": { "example": { "status": "error", "message": "internal server error", "data": "XXXException occured during ..." } } }, "model": str}
    },
    tags=["Extract"],
)
def check_budget(
    datasourcetype: Annotated[str, Body( ..., examples=[ "markdown" ], description="data type")],
    datasourcepath: Annotated[str, Body( ..., examples=[ "/Users/bachtaeyeong/20_DocHub/TIL" ], description="data path" )],
    options: Annotated[dict, Body(
        examples=[
            {
                "ignore_dir_list": [".git", ".vscode", ".obsidian"],
                "reason_model_name": "gemma2:9b-instruct-q5_K_M",
                "embed_model_name": "gemma2:9b-instruct-q5_K_M",
                "max_budget": 1000,
                "shuffle_flag" : True,
                "max_file_num": 10,
                "prompt": "prompt text for generate output from llm",
                "format": "json schema for structured output from llm"
            }
        ],
        description="options, usually not required"
    )],
    service: Annotated[ExtractService, Depends(get_service)]
) -> JSONResponse:
    """
    데이터소스로부터 데이터를 읽고 예산을 추정한다.
    """
    # check, prepare
    ischeck = check_essential_input(datasourcetype, datasourcepath)
    if not ischeck:
        content = ResponseDTO( status='error', message='essential input missing', data='datasourcetype, datasourcepath' )
        return JSONResponse(status_code=400, content=dict(content))
    if 'max_budget' not in options:
        content = ResponseDTO( status='error', message='essential input missing', data='max_budget' )
        return JSONResponse(status_code=400, content=dict(content))
    stuff_default_options(datasourcetype, options)

    # process
    result = service.check_budget(
        datasourcetype,
        datasourcepath,
        options
    )

    # return
    if result['status'] == 'success':
        content = ResponseDTO( status='success', message='data extracted', data=str(result['data']) )
        return JSONResponse(status_code=200, content=dict(content))
    else:
        content = ResponseDTO( status='error', message='data extraction failed', data=str(result['data']) )
        return JSONResponse(status_code=500, content=dict(content))

@router.post(
    "",
    summary="데이터에서 주요개념을 추출한다.",
    description="데이터타입에 따라 데이터소스로부터 데이터를 읽어들인다. 정해진 프롬프트/포맷에 따라 LLM을 활용해 주요개념을 추출한다. 추출한 데이터는 메시지큐로 발행한다.",
    responses={
        status.HTTP_200_OK:                    {"description":"데이터 추출 성공", "content":{ "application/json": { "example": { "status": "success", "message": "data extracted", "data": { "reasoning_sum": 1000, "embedding_sum": 1000, } } } }, "model": ResponseDTO},
        status.HTTP_400_BAD_REQUEST:           {"description":"데이터 추출 실패", "content":{ "application/json": { "example": { "status": "error", "message": "essential input missing", "data": "datatype" } } }, "model": str},
        status.HTTP_422_UNPROCESSABLE_ENTITY:  {"description":"데이터 추출 실패", "content":{ "application/json": { "example": { "status": "error", "message": "input validation error", "data": "" } } }, "model": str},
        status.HTTP_500_INTERNAL_SERVER_ERROR: {"description":"데이터 추출 실패", "content":{ "application/json": { "example": { "status": "error", "message": "internal server error", "data": "XXXException occured during ..." } } }, "model": str}
    },
    tags=["Extract"]
)
def extract(
    datasourcetype: Annotated[str, Body( ..., examples=[ "markdown" ], description="data type")],
    datasourcepath: Annotated[str, Body( ..., examples=[ "/Users/bachtaeyeong/20_DocHub/TIL" ], description="data path" )],
    options: Annotated[dict, Body(
        examples=[
            {
                "ignore_dir_list": [".git", ".vscode", ".obsidian"],
                "reason_model_name": "gemma2:9b-instruct-q5_K_M",
                "embed_model_name": "gemma2:9b-instruct-q5_K_M",
                "max_budget": 1000,
                "shuffle_flag" : True,
                "max_file_num": 10,
                "prompt": "prompt text for generate output from llm",
                "format": "json schema for structured output from llm"
            }
        ],
        description="options, usually not required"
    )],
    service: Annotated[ExtractService, Depends(get_service)],
) -> JSONResponse:
    """
    데이터소스로부터 주요개념을 추출한다
    """
    # check, prepare
    ischeck = check_essential_input(datasourcetype, datasourcepath)
    if not ischeck:
        content = ResponseDTO( status='error', message='essential input missing', data='datasourcetype, datasourcepath' )
        return JSONResponse(status_code=400, content=dict(content))
    stuff_default_options(datasourcetype, options)

    # process
    result = service.extract(
        datasourcetype,
        datasourcepath,
        options
    )

    # return
    if result['status'] == 'success':
        content = ResponseDTO( status='success', message='data extracted', data=str(result['data']) )
        return JSONResponse(status_code=200, content=dict(content))
    else:
        content = ResponseDTO( status='error', message='data extraction failed', data=str(result['data']) )
        return JSONResponse(status_code=500, content=dict(content))

def check_essential_input(datasourcetype, datasourcepath) -> bool:
    """
    필수 입력값을 확인한다.
    """
    if not datasourcetype or not datasourcepath:
        return False
    return True

def stuff_default_options(datasourcetype, options):
    """
    기본 옵션값을 준비한다.
    """
    # 마크다운 데이터타입일때
    if datasourcetype == 'markdown':
        if 'ignore_dir_list' not in options:
            options['ignore_dir_list'] = [
                '.git', '.vscode', '.obsidian', 'assets', 'images', 'img', 'media', 'pictures', 'static', 'uploads',
                'node_modules', 'res', 'resources', 'scripts', 'styles', 'stylesheets', 'test', 'tests', 'tmp'
            ]
    # 모델 이름 기본값
    if 'reason_model_name' not in options:
        options['reason_model_name'] = 'gemma2:9b-instruct-q5_K_M'
    if 'embed_model_name' not in options:
        options['embed_model_name'] = 'gemma2:9b-instruct-q5_K_M'
    pass