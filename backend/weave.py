from typing import Tuple
from model import Concepts
import db
import llmroute as llmroute

def weave_keyconcept_into_networks(operation: str) -> Tuple[int, str]:
    """
    
    """
    rtncd = 900
    rtnmsg = '실패'
    concept_list = db.read_tb_concepts_all()

    if operation == "vector,similarity,top_k":
        for concept in concept_list:
            nearest_list = db.read_tb_concepts_nearest_by_embedding(concept, "cosine_distance", 3)
            for nearest in nearest_list:
                db.create_network_connections_tb_networks(str(concept.id), str(nearest.id))
        
        network_list = db.read_tb_networks_all()
        print(f"network_list num: {len(network_list)}")
        rtncd = 200
        rtnmsg = '성공'
    elif operation == "vector,similarity,top_p":
        
        pass
    elif operation == "vector,similarity,threshold":
        
        pass
    elif operation == "machineread,ordinal_scale":

        pass

    return rtncd, rtnmsg