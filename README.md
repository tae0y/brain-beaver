# README
  
이 프로젝트는 제텔카스텐과 세컨드브레인에서 영감을 받은 **LLM 기반의 지식관리 도구**입니다.\
웹사이트와 마크다운 문서를 처리하는 것이 목표이며, \
문서를 일정한 크기로 분해, 요약, 검증, 연결하여 지식 네트워크를 구성합니다.

이를 통해 **연상법을 활용해 장기기억으로 저장을 유도**하고, \
**연결된 지식으로부터 새로운 아이디어 창출**을 돕습니다.

데이터를 처리하면 아래와 같이 지식 네트워크를 시각화합니다.
![](./demo_001.png)

특정 노드를 선택하면 상세 정보를 조회할 수 있습니다.
![](./demo_002.png)

좌측 상단 패널에서 여러 조회 기능을 제공합니다.
- "Select points in a rectangular area" : 랜덤한 크기의 사각형으로 노드를 선택합니다. 새로운 아이디어를 얻어보세요✨
- "Select the most linked point" : 가장 많이 연결된 지식 노드를 선택합니다. 내 지식의 뿌리를 확인해보세요🕵️‍♂️
- "Select the most linked network" : 랜덤한 네트워크를 선택하여 보여줍니다.

## 설치

1. 저장소를 복제합니다.
    ```bash
    git clone https://github.com/tae0y/brain-beaver.git
    REPOSITORY_ROOT=$(git rev-parse --show-toplevel)
    ```

2. OpenAI(Optional), Naver검색 API(Required) 키를 발급받아 설정합니다.
    ```bash
    # 설정 템플릿 복사
    cd $REPOSITORY_ROOT/src/Python.FastAPI/properties/
    cp secret.sample.properties secret.propertie
    vim secret.properties
    ```
    > OpenAI 키는 선택사항이며, Ollama로 대체할 수 있습니다.

3. docker 폴더로 이동하여 컨테이너를 기동합니다.
    ```bash
    cd $REPOSITORY_ROOT/docker
    docker compose up -d
    ```
    > Docker가 설치되어 있어야 합니다. [Docker 설치 가이드](https://docs.docker.com/desktop/setup/install/mac-install/)를 참고하세요.

4. 다음 앱URL로 접속합니다. 각 관리자 계정 정보는 `docker-compose.yml` 파일에서 확인합니다.
    - UI :beaver: http://localhost:5173
    - Backend :brain: http://localhost:8112/docs
    - DBAdmin :gear: http://localhost:5050
    - DockerAdmin :whale: http://localhost:9000
    - Scheduler ⏰ http://localhost:8080 (데이터백업)
