from common.file import get_file_list_recursively
from common.db import create_keyconcept_into_tb_concepts, update_srctrgnum_tb_concepts_byid
from core.split import split_file_into_keyconcept
from core.weave import weave_keyconcept_into_networks
from core.expand import expand_all_concept_with_websearch
from llm.llmroute import embedd_text, count_tokens
from common.testhelper import sample_file_list
import wandb

rescd, resmsg = expand_all_concept_with_websearch("top", 5) #STAT: 전체대비 5%만 처리
print(f"expand_all_concept_with_websearch : {rescd}, {resmsg}")