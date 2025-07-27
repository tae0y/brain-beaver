# README
  
이 프로젝트는 **LLM 기반의 지식 관리 도구**로, 사용자는 자신의 지식이 **어떻게 분포하고** 있으며 **어디를 보완해야하는지** 알 수 있습니다. 웹URL 혹은 마크다운 문서를 입력하면, 해당 내용을 분석하여 그래프 형태로 시각화합니다. 또한, 오래되거나 잘못된 정보를 식별합니다.

마치 댐을 짓기 위해 통나무를 손질하는 비버처럼:beaver:, 이 프로젝트는 사용자의 데이터를 정제하고, 재구성하며, 확장합니다.

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
    cp secret.sample.properties secret.properties
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
    - 프론트:beaver: http://localhost:5173
    - 백엔드:brain: http://localhost:8112/docs
    - DB관리:gear: http://localhost:5050
    - Docker관리:whale: http://localhost:9000
    - 스케줄러⏰ http://localhost:8080
