import os
from extract.concepts.conceptshandler import ConceptsHandler
from engage.networks.networkshandler import NetworksHandler
from expand.references.referenceshandler import ReferencesHandler

def main():
    conceptHandler = ConceptsHandler()
    networkHandler = NetworksHandler()
    referenceHandler = ReferencesHandler()

    concepts_count_before = conceptHandler.get_concepts_all_count()
    #TODO: 처리내역이 있을 경우 이어서 진행하는 로직 추가
    #if concepts_count_before == 0:
    conceptHandler.extract_keyconcepts_from_datasource(
        datasourcetype='markdown',
        datasourcepath='/Users/bachtaeyeong/20_DocHub/TIL',
        options={
            #'reason_model_name' : 'gemma2:9b-instruct-q5_K_M',
            'reason_model_name' : 'gpt-4o-mini',
            'embed_model_name' : 'text-embedding-3-small',
            'max_file_num' : 1,
            'max_budget_won' : 1000
        }
    )

    # TODO 2 : 코사인유사도 임계값 조정, 유사도 비교하는 로직 변경 등으로 지식간 '연관관계'를 잘 표현할 수 있도록 개선
    networkHandler.engage_keyconcepts_into_networks(
        options={'operation' : 'cosine_distance'}
    )

    conceptHandler.update_concepts_source_target_count()

    # TODO 1 : 웹검색 및 지식확장 로직 구현
    concepts_count_after = conceptHandler.get_concepts_all_count()
    referenceHandler.reset_expand_keyconcpts()
    referenceHandler.expand_keyconcepts_with_websearch(
        options = {
            #'reason_model_name' : 'gemma2:9b-instruct-q5_K_M',
            'reason_model_name' : 'gpt-4o-mini',
            'action_type' : 'top',
            'action_limit' : concepts_count_after//10
        }
    )

    os.system('streamlit run view.py')
    pass

if __name__ == "__main__":
    main()