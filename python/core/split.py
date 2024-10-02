import ray
from llm.llmroute import query_with_context
from common.file import get_plaintext_from_filepath
from common.constants import Constants

constants = Constants.get_instance()

def split_file_into_keyconcept(file_list: list) -> list[dict]:
    keyconcept_list = []
    ray.init()
    with ray.util.multiprocessing.Pool() as pool:
        results = pool.map(extract_keyconcept, file_list)
        for result in results:
            keyconcept_list.extend(result)

    return keyconcept_list

def extract_keyconcept(file_path):
    try:
        file_content = get_plaintext_from_filepath(file_path)

        role = """[ROLE]
        당신은 탁월한 문서 요약 전문가입니다.
        """
        query = """[SYSTEM]
        다음 제시된 문서는 개인적으로 학습한 내용을 정리한 것입니다.
        회고를 돕고 새로운 아이디어를 얻을 수 있도록, 주요내용을 요약하려고 합니다.
        첫째, 핵심되는 내용들을 한 문단으로 작성하세요.
        둘째, 반드시!! 다음 제시된 문서의 내용만을 기준으로 작성하세요.

        다음 응답포맷에 따라 JSON 형식으로 답변하세요.
        {
            "title"    : "명사형으로 끝나는 한 줄 이내의 제목",
            "keywords" : "key1,key2,key3 등 문서에서 추출한 키워드",
            "category" : "정보,감상,질문,착안 중에서 카테고리 선택",
            "summary"  : "기억해둘만한 주요 내용을 한 문단 이내 작성",
        }

        [DOCUMENT]
        """
        context = file_content
        response_list = query_with_context(role + query, file_path, context)
        for response in response_list:
            response['filepath'] = file_path
            response['plaintext'] = file_content

    except Exception as e:
        print(f"extract_keyconcept error: file_path - {e}")
        response_list = []

    return response_list
