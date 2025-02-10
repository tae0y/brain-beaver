from fastapi import APIRouter
from common.models.responseDTO import ResponseDTO
from extract.extractservice import ExtractService

router = APIRouter(
    prefix="/api/extract",
)

class ExtractHandler:
    """
    주요개념 추출과 관련된 요청을 처리한다.

    """
    def __init__(self):
        self.service = ExtractService()
        pass

    @router.post("/check-budget")
    def check_budget(
        self, 
        datasourcetype: str,
        datasourcepath: str,
        options: dict
    ) -> ResponseDTO:
        """
        데이터소스로부터 데이터를 읽고 예산을 추정한다.
        """
        # check, prepare
        self.check_essential_input(datasourcetype, datasourcepath)
        self.stuff_default_options(datasourcetype, options)
        if 'max_budget' not in options:
            raise ValueError("max_budget(KRW) is required")

        # process
        result = self.service.check_budget(
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
        self, 
        datasourcetype: str,
        datasourcepath: str,
        options: dict
    ) -> ResponseDTO:
        """
        데이터소스로부터 주요개념을 추출한다
        """
        # check, prepare
        self.check_essential_input(datasourcetype, datasourcepath)
        self.stuff_default_options(datasourcetype, options)

        # process
        result = self.service.extract(
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

    def check_essential_input(self, datasourcetype, datasourcepath):
        """
        필수 입력값을 확인한다.
        """
        if not datasourcetype or not datasourcepath:
            raise ValueError("datasourcetype is required")
        pass

    def stuff_default_options(self, datasourcetype, options):
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