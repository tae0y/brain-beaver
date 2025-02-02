from extract.concepts.conceptsservice import ConceptsService

class ConceptsHandler:
    """
    주요개념 추출과 관련된 요청을 처리한다.
    """
    # TODO: Controller, Service 레이어 분리

    service : ConceptsService

    def __init__(self):
        self.service = ConceptsService()
        pass

    def extract_keyconcepts_from_datasource(self, datasourcetype, datasourcepath, options: dict):
        """
        데이터소스로부터 주요개념을 추출한다.
        """

        # 데이터 로드
        if (datasourcetype is None) or (datasourcepath is None):
            raise ValueError("datasourcetype or datasourcepath cannot be None.")
        lazy_list = []
        if datasourcetype == 'markdown':
            lazy_list = self.service.get_markdown_lazy_list(datasourcepath)
        elif datasourcetype == 'rssfeed':
            #lazy_list = get_rssfeed_lazy_list(datasourcepath)
            raise NotImplementedError
        elif datasourcetype == 'webpages':
            #lazy_list = get_webpages_lazy_list(datasourcepath)
            raise NotImplementedError


        # 비용 확인
        max_file_num: int
        if 'max_file_num' in options:
            max_file_num = options['max_file_num']
        else:
            max_file_num = 10

        max_budget_won: int
        if 'max_budget_won' in options:
            max_budget_won = options['max_budget_won']
        else:
            max_budget_won = 1000

        cost_testnum = self.service.assume_total_cost(lazy_list, {'max_file_num' : max_file_num})
        cost_total = self.service.assume_total_cost(lazy_list, {})
        if cost_testnum > max_budget_won or cost_total > max_budget_won:
            print(f"LOG-DEBUG: cost_testnum {cost_testnum} cost_total {cost_total}")
            raise ValueError("Cost is too high. Please check the cost.")


        # 주요개념 추출, 저장
        model_name: str
        if 'model_name' in options:
            model_name = options['model_name']
        else:
            model_name = 'gemma2:9b-instruct-q5_K_M'
        for data_name, data_loader in lazy_list[:max_file_num]:
            try:
                self.service.extract_keyconcepts(data_name, data_loader, {'model_name' : model_name})
            except Exception as e:
                print(f"LOG-ERROR: error reading {data_name} - {str(e)}")

        pass

    def update_concepts_source_target_count(self):
        """
        주요개념의 소스/타겟 개수를 갱신한다.
        """
        self.service.update_concepts_source_target_count()
        pass