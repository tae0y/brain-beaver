import common.db as db
import streamlit as st
from streamlit_agraph import agraph, Node, Edge, Config, TripleStore

st.title('Brain Beaver 🦫')

networks = db.read_tb_networks_all()
concepts = db.read_tb_concepts_all()
print(f"networks: {len(networks)}, concepts: {len(concepts)}")

source_count_dict = {}
target_count_dict = {}
for network in networks:
    source_count_dict[network.source] = source_count_dict.get(network.source, 0) + 1
    target_count_dict[network.target] = target_count_dict.get(network.target, 0) + 1

nodes = []
edges = []

node_default_size = 10
node_multiple = 5
node_source_many = '#A3C9A8'
node_neutral = '#69A297'
node_target_many = '#50808E'

#node_type = 'circularImage'
#node_image = 'https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcQTxEQr3SSOrrhOXpbVP0B_4T2OysRy7cGnqA&s'

for concept in concepts:
    node_size = nodes_size = max(node_default_size, 
                                 node_default_size*(source_count_dict.get(concept.id, 1)//node_multiple), 
                                 node_default_size*(target_count_dict.get(concept.id, 1)//node_multiple))
    node_color = node_neutral
    if source_count_dict.get(concept.id, 1) > target_count_dict.get(concept.id, 1)*2:
        node_color = node_source_many
    elif target_count_dict.get(concept.id, 1) > source_count_dict.get(concept.id, 1)*2:
        node_color = node_target_many
    
    nodes.append(Node(
                        id=concept.id,              
                        title=f"{concept.title} | \n{concept.summary.replace('.', '.\n')}",
                        label=concept.id,  
                        color=node_color,
                        shape='circularImage', # image, circularImage, diamond, dot, star, triangle, triangleDown, hexagon, square and icon
                        image='',
                        size=node_size
                    ))

for network in networks:
    edges.append(Edge(
                        source=network.source,      
                        label='',                   
                        target=network.target,
                        color='#ced4da',      
                    ))

config = Config(
                    width=750,
                    height=950,
                    directed=True, 
                    physics=True, 
                    hierarchical=False
                )

rtnmsg = agraph(nodes=nodes, edges=edges, config=config)
#print(rtnmsg)