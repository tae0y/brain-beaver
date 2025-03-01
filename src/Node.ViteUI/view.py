import streamlit as st
import pandas as pd
from cosmograph import cosmo
import kipsum
import random
import string

# Title
st.title('Cosmograph Demo')

# Demo Data
kip = kipsum.Kipsum()
num_of_nodes = 1000
sentences = kip.sentences(num_of_nodes)
points = pd.DataFrame({
    'id': range(1, num_of_nodes+1)
    , 'label': [f'Node {i}' for i in range(num_of_nodes)]
    , 'text': sentences
    , 'value': [random.randint(1, 100) for _ in range(num_of_nodes)]
    , 'category': [random.choice(string.ascii_uppercase) for _ in range(num_of_nodes)]
})

num_of_links = 100
links = pd.DataFrame({
    'source': [random.randint(1, num_of_nodes) for _ in range(num_of_links)]
    , 'target': [random.randint(1, num_of_nodes) for _ in range(num_of_links)]
    , 'value': [random.uniform(0, 2) for _ in range(num_of_links)]
})

# Demo View
widget = cosmo(
  points=points,
  links=links,
  point_id_by='id',
  link_source_by='source',
  link_target_by='target',
  point_color_by='category',
  point_label_by='label',
  point_size_by='value'
)

widget
#widget.fit_view()
#widget.selected_point_ids