from typing import Annotated
from fastapi import APIRouter, Body, Depends
from common.models.responseDTO import ResponseDTO
from extract.extractservice import ExtractService

router = APIRouter(
    prefix="/api/extract",
)

service = ExtractService()
def get_service():
    return service

@router.post("/check-budget")
def check_budget(
    datasourcetype: str = Body( ..., examples=[ { "value": "markdown", "summary": "data type" } ] ),
    datasourcepath: str = Body( ..., examples=[ { "value": "/Users/bachtaeyeong/20_DocHub/TIL", "summary": "data path" } ] ),
    options: dict = Body(
        examples=[
            {
                "value": {
                    "ignore_dir_list": [".git", ".vscode", ".obsidian", "assets", "images", "img", "media", "pictures", "static", "uploads", "node_modules", "res", "resources", "scripts", "styles", "stylesheets", "test", "tests", "tmp"],
                    "reason_model_name": "gemma2:9b-instruct-q5_K_M",
                    "embed_model_name": "gemma2:9b-instruct-q5_K_M",
                    "max_budget": 1000,
                    "shuffle_flag" : True,
                    "max_file_num": 10,
                    "prompt": "prompt text for generate output from llm",
                    "format": "json schema for structured output from llm"
                },
                "summary": "options, usually not required"
            }
        ]
    ),
    service: Annotated[ExtractService, Depends(get_service)] = get_service,
    summary = "데이터소스로부터 데이터를 읽고 예산을 추정한다.",
    description = "데이터타입과 데이터경로를 입력받아, 지연로딩 방식으로 데이터를 조회한다. 데이터 양을 기준으로 LLM 토큰 비용을 추정한다.",
    tags=["Extract"]
) -> ResponseDTO:
    """
    데이터소스로부터 데이터를 읽고 예산을 추정한다.
    """
    # check, prepare
    check_essential_input(datasourcetype, datasourcepath)
    stuff_default_options(datasourcetype, options)
    if 'max_budget' not in options:
        raise ValueError("max_budget(KRW) is required")
    # process
    result = service.check_budget(
        datasourcetype,
        datasourcepath,
        options
    )
    # return
    if result.status == 'success':
        return ResponseDTO(
            status='success',
            message='budget checked',
            data=result.data
        )
    else:
        return ResponseDTO(
            status='error',
            message='budget check failed',
            data=result.data
        )

@router.post("")
def extract(
    datasourcetype: str = Body( ..., examples=[ { "value": "markdown", "summary": "data type" } ] ),
    datasourcepath: str = Body( ..., examples=[ { "value": "/Users/bachtaeyeong/20_DocHub/TIL", "summary": "data path" } ] ),
    options: dict = Body(
        examples=[
            {
                "value": {
                    "ignore_dir_list": [".git", ".vscode", ".obsidian", "assets", "images", "img", "media", "pictures", "static", "uploads", "node_modules", "res", "resources", "scripts", "styles", "stylesheets", "test", "tests", "tmp"],
                    "reason_model_name": "gemma2:9b-instruct-q5_K_M",
                    "embed_model_name": "gemma2:9b-instruct-q5_K_M",
                    "max_budget": 1000,
                    "shuffle_flag" : True,
                    "max_file_num": 10,
                    "prompt": "prompt text for generate output from llm",
                    "format": "json schema for structured output from llm"
                }, 
                "summary": "options, usually not required"
            }
        ]
    ),
    service: Annotated[ExtractService, Depends(get_service)] = get_service,
    summary="데이터소스로부터 주요개념을 추출한다",
    description="데이터타입과 데이터경로를 입력받아, 지연로딩 방식으로 데이터를 조회한다. 정해진 프롬프트와 포맷으로 LLM을 사용해 주요개념을 추출한다. 추출결과는 메시지큐로 발송한다.",
    tags=["Extract"]
) -> ResponseDTO:
    """
    데이터소스로부터 주요개념을 추출한다
    """
    # check, prepare
    check_essential_input(datasourcetype, datasourcepath)
    stuff_default_options(datasourcetype, options)
    # process
    result = service.extract(
        datasourcetype,
        datasourcepath,
        options
    )
    # return
    if result.status == 'success':
        return ResponseDTO(
            status='success',
            message='data extracted',
            data=result.data
        )
    else:
        return ResponseDTO(
            status='error',
            message='data extraction failed',
            data=result.data
        )

def check_essential_input(datasourcetype, datasourcepath):
    """
    필수 입력값을 확인한다.
    """
    if not datasourcetype or not datasourcepath:
        raise ValueError("datasourcetype is required")
    pass

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