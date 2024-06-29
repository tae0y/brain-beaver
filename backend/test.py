import db

concept_list = db.read_tb_concepts_all()
nearest = db.read_tb_concepts_by_embedding(concept_list[0].id, "top_k")