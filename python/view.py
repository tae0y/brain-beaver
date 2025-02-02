import streamlit as st
from streamlit_agraph import agraph, Node, Edge, Config, TripleStore
import math
from extract.concepts.conceptsservice import ConceptsService
from engage.networks.networksservice import NetworksService

st.title('Brain Beaver 🦫')

# 서비스 객체 생성
concepts_service = ConceptsService()
networks_service = NetworksService()

# 데이터 조회
networks = networks_service.read_networks_all()
concepts = concepts_service.read_concepts_all()
references = [] #concepts_service.repository.read_tb_references_all()
print(f"networks: {len(networks)}, concepts: {len(concepts)}, references: {len(references)}")

nodes = []
edges = []

node_default_size = 10
node_multiple = 5
node_source_many = '#A3C9A8'
node_neutral = '#69A297'
node_target_many = '#50808E'

# 사이드바 컨테이너 생성
detail_container = st.sidebar.container()

# 노드 생성 부분에서 데이터 저장
concepts_dict = {}

for concept in concepts:
    node_size = node_default_size

    node_color = node_neutral
    if concept.source_num > concept.target_num * 2:
        node_color = node_source_many
    elif concept.target_num > concept.source_num * 2:
        node_color = node_target_many

    # concepts_dict에 개념 정보 저장
    concepts_dict[f"C{concept.id}"] = {
        "title": concept.title,
        "id": concept.id,
        "keywords": concept.keywords,
        "category": concept.category,
        "summary": concept.summary,
        "data_name": concept.data_name,
        "source_num": concept.source_num,
        "target_num": concept.target_num
    }

    nodes.append(Node(
                        id=f"C{concept.id}",
                        title=f"{concept.title[:20]}",
                        label=concept.id,  
                        color=node_color,
                        shape='circularImage', # image, circularImage, diamond, dot, star, triangle, triangleDown, hexagon, square and icon
                        image='',
                        size=node_size
                    ))

for reference in references:
    nodes.append(Node(
                        id=f"R{reference.id}",
                        title=f"{reference.concept_id} : {reference.description[:200].replace('.','.\n')}",
                        label=reference.id,  
                        color='#FF0000',
                        shape='dot', # image, circularImage, diamond, dot, star, triangle, dot, hexagon, square and icon
                        image='',
                        size=node_default_size*1.3
                    ))
    edges.append(Edge(
                        source=f"R{reference.id}",
                        label='',
                        target=f"C{reference.concept_id}",
                        color='#ced4da',
                    ))

for network in networks:
    edges.append(Edge(
                        source=f"C{network.source_concept_id}",
                        label='',
                        target=f"C{network.target_concept_id}",
                        color='#ced4da',
                    ))

config = Config(
                    width=750,
                    height=950,
                    directed=True, 
                    physics=True, 
                    maxVelocity=60,
                    hierarchical=False
                )

# 그래프 렌더링 및 클릭 이벤트 받기
clicked_node = agraph(nodes=nodes, edges=edges, config=config)

# 클릭된 노드 정보 표시
if clicked_node:
    with detail_container:
        st.header("상세 정보")
        if clicked_node.startswith('C'):
            node_info = concepts_dict.get(clicked_node)
            if node_info:
                st.write("**Title:**", node_info["title"])
                st.write("**ID:**", node_info["id"])
                st.write("**Keywords:**", node_info["keywords"])
                st.write("**Category:**", node_info["category"])
                st.write("**Summary:**", node_info["summary"].replace('\n', ' '))
                st.write("**Data name:**", node_info["data_name"])
                st.write("**Source connections:**", node_info["source_num"])
                st.write("**Target connections:**", node_info["target_num"])
        elif clicked_node.startswith('R'):
            st.write("Reference node details will be displayed here")
