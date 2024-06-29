from common.file import get_file_list_recursively
from common.db import create_keyconcept_into_tb_concepts, create_network_connections_tb_networks
from core.split import split_file_into_keyconcept
from core.weave import weave_keyconcept_into_networks
from llm.llmroute import embedd_text, count_tokens
from common.testhelper import sample_file_list

# 1. 파일목록을 추출한다.
root_dir = '/Users/bachtaeyeong/20_DocHub/TIL'
ignore_dir_list = ['.git','Res','.obsidian','Chats','.DS_Store','.gitignore']
file_list = get_file_list_recursively(root_dir, ignore_dir_list)
file_list = [file for file in file_list if file.endswith('.md') ]
file_list = sample_file_list(file_list=file_list, bucket_size=10) #파일 랜덤 샘플링
for file in file_list:
    print(file)

# 2. 파일에서 주요 컨셉을 추출하고 저장한다
keyconcept_list = split_file_into_keyconcept(file_list=file_list, limit_file_count=0) #처리할 건수 지정
keyconcept_list = [dict(
    title    = keyconcept.get('title',''),
    keywords = keyconcept.get('keywords',''),
    category = keyconcept.get('category',''),
    summary  = keyconcept.get('summary',''),
    token_num = count_tokens(keyconcept.get('summary','')),
    embedding = embedd_text(keyconcept.get('summary',''))
) for keyconcept in keyconcept_list]
rescd, resmsg = create_keyconcept_into_tb_concepts(keyconcept_list)
print(f"{rescd}, {resmsg}")

# 3. 주요 컨셉들간 네트워크 관계를 저장한다
keyconcept_networks = weave_keyconcept_into_networks("vector,similarity,threshold")
rescd, resmsg = create_network_connections_tb_networks(keyconcept_networks)
print(f"{rescd}, {resmsg}")