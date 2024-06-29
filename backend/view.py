import db
import streamlit
from streamlit_agraph import agraph, Node, Edge, Config, TripleStore

networks = db.read_tb_networks_all()
concepts = db.read_tb_concepts_all()

nodes = []
edges = []

for concept in concepts:
    nodes.append(Node(id=concept['id'], 
                      label=concept.title, 
                      size=10, 
                      shape='dot',
                      color='red'))

for network in networks:
    edges.append(Edge(source=network['source'], 
                      target=network['target'], 
                      label=''))

config = Config(width=750,
                height=950,
                directed=True, 
                physics=True, 
                hierarchical=True,
                # **kwargs
                )

return_value = agraph(nodes=nodes, 
                      edges=edges, 
                      config=config)