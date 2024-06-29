import common.db as db
import streamlit as st
from streamlit_agraph import agraph, Node, Edge, Config, TripleStore

st.title('Brain Beaver 🦫')

networks = db.read_tb_networks_all()
concepts = db.read_tb_concepts_all()
print(f"networks: {len(networks)}, concepts: {len(concepts)}")

nodes = []
edges = []

#TODO: 연결된 노드가 많으면 색상과 크기를 조정
for concept in concepts:
    nodes.append(Node(
                        id=concept.id,              
                        title=f"{concept.title} | \n{concept.summary.replace('.', '.\n')}",
                        label=concept.id,  
                        color='#ACDBC9',
                        shape='square',             
                        size=10,                    
                    ))

for network in networks:
    edges.append(Edge(
                        source=network.source,      
                        label='',                   
                        target=network.target      
                    ))

config = Config(
                    width=750,
                    height=950,
                    directed=True, 
                    physics=True, 
                    hierarchical=False
                )

rtnmsg = agraph(nodes=nodes, edges=edges, config=config)
print(rtnmsg)