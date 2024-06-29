import db
import streamlit as st
from streamlit_agraph import agraph, Node, Edge, Config, TripleStore

st.title('Brain Beaver 🦫')

networks = db.read_tb_networks_all()
concepts = db.read_tb_concepts_all()
print(f"networks: {len(networks)}, concepts: {len(concepts)}")

nodes = []
edges = []

for concept in concepts:
    nodes.append(Node(
                        id=concept.id,              
                        title=f"{concept.title} | {concept.summary}",      
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