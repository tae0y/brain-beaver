#from extract.concepts.conceptsservice import ConceptsService #순환참조 발생으로 각주처리
from networks.networksrepository import NetworksRepository
from common.llmroute.llmrouter import LLMRouter
from common.algebra.algebra import cosine_similarity
import traceback

class NetworksService:
    #conceptService : ConceptsService
    repository : NetworksRepository
    llmclients : dict

    def __init__(self):
        self.repository = NetworksRepository()
        #conceptService = ConceptsService()

        llmrouter = LLMRouter()
        self.llmclients = llmrouter.get_clients_all()
        pass

    def engage_keyconcepts_into_networks(self, options: dict):
        """
        주요개념을 네트워크로 연결한다

        - options
            - operation : str
                - 'cosine_distance' : 코사인 거리를 이용한 유사도 측정
                - 'max_inner_product' : 내적을 이용한 유사도 측정
                - 'l1_distance' : L1 거리를 이용한 유사도 측정
        """
        from concepts.conceptsservice import ConceptsService
        conceptService = ConceptsService()

        operation : str
        if 'operation' in options:
            operation = options['operation']
        else:
            operation = 'cosine_distance'

        # 네트워크 관계 저장
        result = conceptService.get_concepts()
        cosine_sim_check = options['cosine_sim_check'] if 'cosine_sim_check' in options else "false"
        if result['status'] == 'success':
            keyconcepts = result['data']
            for c in keyconcepts:
                try:
                    # TODO: 연관성을 검사하는 것은 아니고, 의미적 유사도를 측정하는 것임. 연관성, 찬/반을 따지려면 어떻게 해야할까??
                    nearest_list = conceptService.read_concepts_nearest_by_embedding(c, operation, 3)
                    for nearest in nearest_list['data']:
                        if cosine_sim_check == "true" and cosine_similarity(c.embedding, nearest.embedding) > 0.7:
                            self.repository.create_network_connections_tb_networks(str(c.id), str(nearest.id))
                        elif cosine_sim_check == "false":
                            self.repository.create_network_connections_tb_networks(str(c.id), str(nearest.id))
                except Exception as e:
                    traceback.print_exc()
                    continue
        else:
            raise Exception('fail to get concepts')

    def read_networks_all(self):
        return self.repository.read_tb_networks_all()

    def delete_networks_all(self):
        return self.repository.delete_tb_networks_all()