from extract.concepts.conceptshandler import ConceptsHandler
from engage.networks.networkshandler import NetworksHandler

def main():
    conceptHandler = ConceptsHandler()
    networkHandler = NetworksHandler()

    conceptHandler.extract_keyconcepts_from_datasource(
        datasourcetype='markdown',
        datasourcepath='/Users/bachtaeyeong/20_DocHub/TIL',
        options={
            'model_name' : 'gemma2:9b-instruct-q5_K_M',
            'max_file_num' : 2,
            'max_budget_won' : 1000
        }
    )

    networkHandler.engage_keyconcepts_into_networks(
        options={'operation' : 'cosine_distance'}
    )

    conceptHandler.update_concepts_source_target_count()

if __name__ == "__main__":
    main()