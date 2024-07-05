from common.file import get_file_list_recursively
from common.db import create_keyconcept_into_tb_concepts, update_srctrgnum_tb_concepts_byid
from core.split import split_file_into_keyconcept
from core.weave import weave_keyconcept_into_networks
from core.expand import expand_all_concept_with_websearch
from llm.llmroute import embedd_text, count_tokens
from common.testhelper import sample_file_list
import wandb
import os
from common.constants import Constants

"""
로거 시작!
"""
constans = Constants.get_instance()

os.environ['WANDB_MODE'] = 'offline'
#os.environ['WANDB_MODE'] = 'online'

wandb.login() #모드에 맞는 API 키값 입력
wandb.init(
    project="brain-beaver",

    config={
    #"learning_rate": 0.02,
    #"architecture": "CNN",
    #"dataset": "CIFAR-100",
    #"epochs": 10,
    }
)

"""
비즈니스 로직
"""
try:
    # 1. 파일목록을 추출한다.
    #TODO: 로컬파일 대신 RSS, 웹크롤링
    #root_dir = '/Users/bachtaeyeong/20_DocHub/TIL'
    root_dir = '/Users/bachtaeyeong/20_DocHub/TIL'
    ignore_dir_list = ['.git','Res','.obsidian','Chats','.DS_Store','.gitignore', '구직']
    file_list = get_file_list_recursively(root_dir, ignore_dir_list)
    file_list = [file for file in file_list if file.endswith('.md') ]
    file_list = sample_file_list(file_list=file_list, bucket_size=1) #STAT: 파일 랜덤 샘플링
    #for file in file_list:
    #    print(file)
    print(f"file_list num : {len(file_list)}")

    # 2. 파일에서 주요 컨셉을 추출하고 저장한다
    #TODO: 로깅 파일로 저장, 로그파일명은 날짜시간으로, 각 로그는 날짜-시간-파일명-상태-메시지
    #TODO: checkpoints, 중단된 파일부터 다시 시작
    keyconcept_list = split_file_into_keyconcept(file_list=file_list[:5]) #STAT: 처리할 건수 지정
    keyconcept_list = [dict(
        title    = keyconcept.get('title',''),
        keywords = keyconcept.get('keywords',''),
        category = keyconcept.get('category',''),
        summary  = keyconcept.get('summary',''),
        token_num = count_tokens(keyconcept.get('summary','')),
        embedding = embedd_text(keyconcept.get('summary','')),
        datasource = root_dir,
        filepath = keyconcept.get('filepath',''),
        plaintext = keyconcept.get('plaintext','')
    ) for keyconcept in keyconcept_list]
    rescd, resmsg = create_keyconcept_into_tb_concepts(keyconcept_list) #split_file_into_keyconcept 내부로
    print(f"create_keyconcept_into_tb_concepts : {rescd}, {resmsg}")

    # 3. 주요 컨셉들간 네트워크 관계를 저장한다
    rescd, resmsg = weave_keyconcept_into_networks("vector,similarity,threshold")
    print(f"weave_keyconcept_into_networks : {rescd}, {resmsg}")

    rescd, resmsg = update_srctrgnum_tb_concepts_byid() #weave_keyconcept_into_networks 내부로
    print(f"update_srctrgnum_tb_concepts_byid : {rescd}, {resmsg}")

    # 4. 컨셉들에 반대되는 내용을 웹에서 검색하여 저장한다
    #TODO: 병렬처리
    rescd, resmsg = expand_all_concept_with_websearch("top", len(keyconcept_list)//20) #STAT: 전체대비 5%만 처리
    print(f"expand_all_concept_with_websearch : {rescd}, {resmsg}")

except Exception as e:
    print(f"error: {e}")
finally:
    """
    로거 종료!
    """
    wandb.finish()