import os
import sys
import json
import certifi
import urllib.request
from common.db import SessionLocal, create_reference_into_tb_references
from common.model import References
from common.model import Concepts
from llm.llmroute import query_with_context
from common.constants import Constants
import traceback
from typing import Tuple
from concurrent.futures import ThreadPoolExecutor

def expand_all_concept_with_websearch(action_type:str="all", limit:int=10) -> Tuple[int, str]:
    rescd = 900
    resmsg = '실패'

    # 데이터 조회
    session = SessionLocal()
    try:
        if action_type == "top":
            query = session.query(Concepts).order_by(Concepts.target_num.desc()).limit(limit)
        elif action_type == "all":
            query = session.query(Concepts)

        concpets_list = query.all()
        
        # 예외, 실패카운트 함수화
        global fail_count
        def expand_and_handle_exceptions(concept):
            try:
                return expand_one_concept_with_websearch(concept)
            except Exception as e:
                print(f"Error during response parsing for expand_one_concept_with_websearch: {e}")
                traceback.print_exc()
                fail_count += 1
                return None  # 실패한 경우 None 반환

        # 병렬 처리
        with ThreadPoolExecutor(max_workers=10) as executor:
            results = list(executor.map(expand_and_handle_exceptions, concpets_list))

        # 결과 처리 
        successful_results = [result for result in results if result is not None]

        rescd = 200
        resmsg = f'성공 ({len(concpets_list)}건 중 {len(successful_results)}건 성공)'
    except Exception as e:
        concpets_list = []
        rescd = 900
        resmsg = '실패'
    finally:
        session.close()
    

    return rescd, resmsg


def expand_one_concept_with_websearch(concept: Concepts):
    try:
        # Constants
        constants = Constants.get_instance()

        #--------------------------------------------------------------------------------------------------------
        # 데이터 조회
        #session = SessionLocal()
        #try:
        #    query = session.query(Concepts)
        #    concpets_list = query.all()
        #except Exception as e:
        #    concpets_list = []
        #finally:
        #    session.close()
        #concept = concpets_list[94]
        print('\n\n-------------------------------------------------------------------------------------------------')
        print(f">> 처리대상\n {concept}")


        #--------------------------------------------------------------------------------------------------------
        # 검색어 생성
        context = f"{concept.summary}"
        search_keyword_list = query_with_context("""
        [ROLE]
        당신은 냉소적인 소프트웨어 엔지니어입니다.
        주니어 엔지니어의 허황된 목표를 비웃으며, 그들이 무엇을 잘못하고 있는지 지적하세요.
        정중한 태도로, 그들이 무엇을 더 배워야 하는지 알려주세요.

        [SYSTEM]
        다음 제시된 [OPINION]을 냉소적이며 강하게 반대하는 opposition을 작성하고,
        해당 주장을 검색하기 위한 keywords를 나열하세요.

        다음 응답포맷에 따라 JSON 형식으로 답변하세요.
        {
            "opposition" : "예시) 당연히 무엇무엇이 아니며, 무엇무엇이다!",
            "keywords"   : "예시) 검색 키워드 나열"
        }

        [OPINION]
        """, context)
        print('\n\n-------------------------------------------------------------------------------------------------')
        print(f">> 검색어\n {search_keyword_list}")
        opposition = search_keyword_list[0]['opposition']
        search_keyword = search_keyword_list[0]['keywords']

        #--------------------------------------------------------------------------------------------------------
        # 웹 검색
        client_id = constants.naver_client_id
        client_secret = constants.naver_client_secret
        encText = urllib.parse.quote(search_keyword)
        url = constants.naver_webkr_url + encText

        request = urllib.request.Request(url)
        request.add_header("X-Naver-Client-Id",client_id)
        request.add_header("X-Naver-Client-Secret",client_secret)
        response = urllib.request.urlopen(request, cafile=certifi.where())
        rescode = response.getcode()

        if(rescode==200):
            response_body = response.read()
            #print(response_body.decode('utf-8'))
            with open('./res/websearch.json', 'w', encoding="utf-8") as f:
                f.write(response_body.decode('utf-8'))
        else:
            print("Error Code:" + rescode)

        with open('./res/websearch.json', 'r') as f:
            jsonraw = f.read()
        jsonobj = json.loads(jsonraw)

        print('\n\n-------------------------------------------------------------------------------------------------')
        print(f">> 웹검색 건수는! \n {len(jsonobj['items'])}")
        print(f">> 웹검색 전문은! \n {str(jsonobj['items'])}\n\n\n")


        #--------------------------------------------------------------------------------------------------------
        # 비교/검증
        comparison_list = []
        for item in jsonobj['items']:
            try:
                #TIP: 맥락정보를 유지하기 위해 persona를 가정
                result = query_with_context("""
                [ROLE]
                당신은 중립적인 검증자입니다.
                검증은 오로지 정확한 사실에 기반하여 이루어져야 한다고 믿습니다.
                추정과 가정은 검증에 방해가 될 수 있다는 것을 명심하세요.

                [SYSTEM]
                제시된 [DOCUMENT]가 [OPINION]의 내용과 정확하게 일치하는지 확인하세요.
                다음 응답 포맷에 따라 각 문서에 대한 검증 결과를 JSON 형식으로 답변하세요.

                {
                    "persona"  : "[DOCUMENT]를 작성한 사람의 배경과 특성을 두 문장으로 기술"
                    "decision" : "예시) True or False",
                    "detailed" : "예시) 검증 결과에 대해 한 문단 이내로 상세히 기술"
                } 

                [OPINION]
                """+opposition+"""" 
                
                [DOCUMENT]
                """, f"{item["title"]} - {item["description"]}")
                print('result > {result}')
                comparison_list.append(
                    {
                        "persona"  : result[0]['persona'],
                        "decision" : result[0]['decision'],
                        "detailed" : result[0]['detailed']
                    }
                )
            except Exception as e:
                print(f"Error during response parsing for comparison_list: {e}")
                continue
            
        print('\n\n-------------------------------------------------------------------------------------------------')
        print(f">> 비교/검증\n {str(comparison_list)}")


        #--------------------------------------------------------------------------------------------------------
        # 다중 전문가 모델
        final_result = query_with_context("""
        [ROLE]
        당신은 냉철한 중재자입니다.

        [SYSTEM]
        다수의 소프트웨어 엔지니어들이 각자의 의견을 제시하고 있습니다.
        이들의 의견을 종합하여 임원에게 보고할 내용을 서식 없이 한국어로 작성하세요.
        각 주장에 대한 검증 결과를 종합하여, 
        최종 결론를 두 문장으로 요약하여 제시하세요.

        [DOCUMENT]
        """, str(comparison_list), options={'api_type':'generate', 
                 'chunk_size':8000,
                 'format':None,})

        true_count = 0
        false_count = 0
        for item in comparison_list:
            if item['decision'] == 'True':
                true_count += 1
            else:
                false_count += 1

        print('\n\n-------------------------------------------------------------------------------------------------')
        print(f">> 다수결\n {opposition} = {true_count > false_count}")
        print(f">> 다중 전문가 모델\n {final_result[0]}")

        print('\n\n-------------------------------------------------------------------------------------------------')
        if true_count > false_count:
            reference_list = []
            reference_list.append({
                'concept_id':concept.id,
                'description':f"{final_result[0]} -> {str(comparison_list)}"
            })

            rtncd, rtnmsg = create_reference_into_tb_references(reference_list)
            print(f">> 결과 저장\n {rtncd} : {rtnmsg}")
    except Exception as e:
        print(f"Error during response parsing for expand_concept_with_websearch: {e}")
        traceback.print_exc()
        pass
    
    return