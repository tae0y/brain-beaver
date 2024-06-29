from typing import Tuple
from model import Concepts
import db
import llmroute
import algebra 

def weave_keyconcept_into_networks(operation: str) -> Tuple[int, str]:
    """
    
    """
    rtncd = 900
    rtnmsg = '실패'
    concept_list = db.read_tb_concepts_all()

    if operation == "vector,similarity,top_k":
        for concept in concept_list:
            #여기에서 top_k를 찾는 방법을 정한다 : cosine_distance, max_inner_product, l1_distance
            nearest_list = db.read_tb_concepts_nearest_by_embedding(concept, "cosine_distance", 3)
            for nearest in nearest_list:
                db.create_network_connections_tb_networks(str(concept.id), str(nearest.id))
        
        network_list = db.read_tb_networks_all()
        print(f"network_list num: {len(network_list)}")
        rtncd = 200
        rtnmsg = '성공'
    elif operation == "vector,similarity,threshold":
        for concept in concept_list:
            #여기에서 top_k를 찾는 방법을 정한다 : cosine_distance, max_inner_product, l1_distance
            nearest_list = db.read_tb_concepts_nearest_by_embedding(concept, "cosine_distance", 3)
            for nearest in nearest_list:
                if algebra.cosine_similarity(concept.embedding, nearest.embedding) > 0.7:
                    db.create_network_connections_tb_networks(str(concept.id), str(nearest.id))
        pass
    elif operation == "vector,similarity,top_p":
        
        pass
    elif operation == "machineread,ordinal_scale":

        pass

    return rtncd, rtnmsg