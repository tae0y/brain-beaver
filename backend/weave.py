from typing import Tuple
from model import Concepts
import db
import llmroute
import algebra 
import traceback

def weave_keyconcept_into_networks(operation: str) -> Tuple[int, str]:
    """
    
    """
    rtncd = 900
    rtnmsg = '실패'
    concept_list = db.read_tb_concepts_all()

    if operation == "vector,similarity,top_k":
        success_cnt = 0
        for concept in concept_list:
            try:
                #여기에서 top_k를 찾는 방법을 정한다 : cosine_distance, max_inner_product, l1_distance
                nearest_list = db.read_tb_concepts_nearest_by_embedding(concept, "cosine_distance", 3)
                for nearest in nearest_list:
                    db.create_network_connections_tb_networks(str(concept.id), str(nearest.id))
                success_cnt+=1
            except Exception as e:
                traceback.print_exc()
                continue
        
        network_list = db.read_tb_networks_all()
        print(f"network_list num: {len(network_list)}")
        rtncd = 200
        rtnmsg = f'성공 ({len(concept_list)}중 {success_cnt})건 처리됨)'
    elif operation == "vector,similarity,threshold":
        success_cnt = 0
        try:
            for concept in concept_list:
                #여기에서 top_k를 찾는 방법을 정한다 : cosine_distance, max_inner_product, l1_distance
                nearest_list = db.read_tb_concepts_nearest_by_embedding(concept, "cosine_distance", 3)
                for nearest in nearest_list:
                    if algebra.cosine_similarity(concept.embedding, nearest.embedding) > 0.7:
                        db.create_network_connections_tb_networks(str(concept.id), str(nearest.id))
                success_cnt+=1
        except Exception as e:
            traceback.print_exc()
            pass        
        
        network_list = db.read_tb_networks_all()
        print(f"network_list num: {len(network_list)}")
        rtncd = 200
        rtnmsg = f'성공 ({len(concept_list)}중 {success_cnt})건 처리됨)'
        pass
    elif operation == "vector,similarity,top_p":
        
        pass
    elif operation == "machineread,ordinal_scale":

        pass

    return rtncd, rtnmsg