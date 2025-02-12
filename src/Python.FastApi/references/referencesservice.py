import traceback
import urllib.request
import certifi
import json
from concepts.conceptsmodel import Concepts
from references.referencesrepository import ReferencesRepository
from common.llmroute.llmrouter import LLMRouter
from common.llmroute.baseclient import BaseClient
from common.system.constants import Constants
from concurrent.futures import ThreadPoolExecutor
from common.llmroute.openaiclient import OpenAIClient
from common.llmroute.ollamaclient import OllamaClient

class ReferencesService:
    """
    references 로직을 처리한다.
    """
    def __init__(self):
        self.repository = ReferencesRepository()
        self.constants = Constants.get_instance()
        self.llmroute = LLMRouter()

    def delete_refereces_all(self):
        """
        expand_keyconcpts 테이블을 초기화한다.
        """
        self.repository.delete_tb_references_all()
        pass

    def read_references_all(self):
        """
        모든 references를 조회한다.
        """
        return self.repository.read_tb_references_all()

    def expand_keyconcepts_with_websearch(self, options: dict):
        """
        주요개념 확장을 위해 웹검색을 수행하고 저장한다
        """
        from concepts.conceptsservice import ConceptsService
        conceptService = ConceptsService()
        action_type = options['action_type'] if 'action_type' in options else 'all'
        action_limit = options['action_limit'] if 'action_limit' in options else 10

        concepts = []
        if action_type == 'top':
            concepts.extend(conceptService.read_concpets_top_by_source_target_num(action_limit))
        elif action_type == 'all':
            concepts.extend(conceptService.get_concepts())

        # 검색 병렬 처리
        reason_model_name = options['reason_model_name'] if 'reason_model_name' in options else 'gemma2:9b-instruct-q5_K_M'
        llmclient = self.llmroute.get_client_by_modelname(reason_model_name)
        #TODO : 프로그레스바 추가
        #TODO : 비용추계 추가
        results = []
        for concept in concepts:
            results.append(self.expand_one_concept_with_websearch(concept, llmclient))
        #TODO : OpenAI의 경우 병렬호출, 그외에는 웹검색만 병렬호출
        #pool = ThreadPoolExecutor(max_workers=self.constants.thread_global_thread_pool)
        #results = list(
        #        pool.map(
        #            lambda concept: self.expand_one_concept_with_websearch(concept, llmclient), concepts
        #        )
        #    )

        # 결과 확인
        successful_results = [result for result in results if result is not None]
        print(f"LOG-DEBUG {len(successful_results)}건 처리됨)")


    def expand_one_concept_with_websearch(self, concept : Concepts, llmclient : BaseClient):
        """
        주요개념 하나에 대해 웹검색을 수행하고 저장한다
        """
        try:
            #--------------------------------------------------------------------------------------------------------
            # 검색어 준비
            headless_format_keyword = {
                                "type" : "object",
                                "properties" : {
                                    "opposition" : {
                                        "description" : "opposition text",
                                        "type" : "string"
                                    },
                                    "keywords" : {
                                        "description" : "search keywords separated with comma. it will be used for junior engineer to search web and understand opposition text.",
                                        "type" : "string"
                                    },
                                },
                                "required" : ["opposition", "keywords"],
                                "additionalProperties" : False
                            }
            full_format_keyword = {
                        "type" : "json_schema",
                        "json_schema" : {
                            "name" : "response_schema",
                            "schema" : headless_format_keyword
                        }
                    }
            if isinstance(llmclient, OpenAIClient):
                format = full_format_keyword
            elif isinstance(llmclient, OllamaClient):
                format = headless_format_keyword

            keyword_gen_results = llmclient.generate(
                prompt = """
                        당신은 최고의 기술기업에서 기술의사결정을 책임지는 CTO입니다.
                        오늘은 주니어 엔지니어의 멘토링을 위해 '악마의 대변인' 역할을 맡았습니다.
                        주니어 엔지니어의 기술 설명을 듣고, 합리적으로 그와 반대되는 의견을 제시해야합니다.

                        다음 제시된 [DOCUMENT]를 분석하고,
                        합리적으로 그와 반대되는 의견을 작성합니다.
                        주니어가 해당 의견을 이해하기 위해 검색할 키워드도 함께 제시합니다.
                        다음 포맷에 맞추어 JSON 형식으로 답변하세요.
                        {
                            "opposition" : "예시) 당연히 무엇무엇이 아니며, 무엇무엇이다!",
                            "keywords"   : "예시) 검색 키워드 나열"
                        }

                        [DOCUMENT]
                        """ + concept.summary,
                options = {
                    'format' : format
                }
            ).data

            opposition : str
            search_keyword : str
            if len(keyword_gen_results) != 0:
                opposition = keyword_gen_results['opposition']
                search_keyword = keyword_gen_results['keywords']
                if opposition is None or search_keyword is None:
                    return None
            else:
                return None
            print(f"LOG-DEBUG : 반대의견 및 검색어 생성결과 - {keyword_gen_results}")

            #--------------------------------------------------------------------------------------------------------
            # 웹 검색
            client_id = self.constants.naver_client_id
            client_secret = self.constants.naver_client_secret
            encText = urllib.parse.quote(search_keyword)
            url = self.constants.naver_webkr_url + encText

            request = urllib.request.Request(url)
            request.add_header("X-Naver-Client-Id",client_id)
            request.add_header("X-Naver-Client-Secret",client_secret)
            response = urllib.request.urlopen(request, cafile=certifi.where())
            rescode = response.getcode()

            if(rescode==200):
                response_body = response.read()
                #print(response_body.decode('utf-8'))
                #with open('websearch_results.json', 'w', encoding="utf-8") as f:
                #    f.write(response_body.decode('utf-8'))
            else:
                print(f"LOG-ERROR : {rescode} in expand_one_concept_with_websearch")
            jsonobj = json.loads(response_body)

            #--------------------------------------------------------------------------------------------------------
            # 비교검증
            comparison_list = []
            for item in jsonobj['items']:
                # 검색결과가 주장에 부합하는지
                headless_format_compare = {
                                    "type" : "object",
                                    "properties" : {
                                        "persona" : {
                                            "description" : "persona of the document writer",
                                            "type" : "string"
                                        },
                                        "decision" : {
                                            "description" : "True or False",
                                            "type" : "string"
                                        },
                                        "detailed" : {
                                            "description" : "detailed description of the decision",
                                            "type" : "string"
                                        },
                                    },
                                    "required" : ["persona", "decision", "detailed"],
                                    "additionalProperties" : False
                                }
                full_format_compare = {
                            "type" : "json_schema",
                            "json_schema" : {
                                "name" : "response_schema",
                                "schema" : headless_format_compare
                            }
                        }
                if isinstance(llmclient, OpenAIClient):
                    format = full_format_compare
                elif isinstance(llmclient, OllamaClient):
                    format = headless_format_compare

                result = llmclient.generate(
                    prompt = """
                            당신은 최고의 기술기업에서 기술의사결정을 책임지는 CTO입니다.
                            오늘은 주니어 엔지니어들의 타운홀 기술 토론회에서 중립적인 검증자로 참여합니다.
                            주니어 엔지니어들의 기술 설명을 듣고,
                            근거로 제시한 [DOCUMENT]가 [OPINITON]을 지지하는지 검증합니다.
                            다음 제시된 형식에 맞춰
                            [DOCUMENT]를 작성한 사람의 기술적 성향을 파악하고
                            검증 결과 및 그 상세 내용을 기술합니다.
                            {
                                "persona"  : "[DOCUMENT]를 작성한 사람의 배경과 특성을 두 문장으로 기술"
                                "decision" : "예시) True or False",
                                "detailed" : "예시) 검증 결과에 대해 한 문단 이내로 상세히 기술"
                            }
                            [OPINION]
                            """ + opposition + """
                            [DOCUMENT]
                            """ + item['title'] + " " + item['description'],
                    options = {
                        'format' : format
                    }
                ).data
                comparison_list.append(
                    {
                        "persona"  : result['persona'],
                        "decision" : result['decision'],
                        "detailed" : result['detailed']
                    }
                )
            print(f"LOG-DEBUG : 검색결과/주장 부합여부 - {str(comparison_list)}")

            # 검색결과의 내용을 종합
            final_result = llmclient.generate(
                prompt = """
                당신은 최고의 기술기업에서 기술의사결정을 책임지는 CTO입니다.
                격론이 오가는 기술 토론회에서 다수의 소프트웨어 엔지니어들이 각자의 의견을 제시하고 있습니다.
                이들의 의견을 종합하여 회사의 명확한 기술 지침을 정해야합니다.
                각자의 주장에 대한 검증 결과를 참고하여, 최종 결론을 두 문장으로 제시하세요.
                [DOCUMENT]
                """ + str(comparison_list),
                options = {}
            ).data['text']
            print(f"LOG-DEBUG : 검색결과 종합결과 - {final_result}")

            # 다수결로 인용 결정
            true_count = 0
            false_count = 0
            for item in comparison_list:
                if item['decision'] == 'True':
                    true_count += 1
                else:
                    false_count += 1

            # 결과 저장
            if true_count > false_count:
                reference_list = []
                reference_list.append({
                    "concept_id" : concept.id,
                    "description" : f"종합의견: {final_result} / 상세의견: {str(comparison_list)}"
                })
                self.repository.create_reference_into_tb_references(reference_list)

            return final_result
        except Exception as e:
            traceback.print_exc()
