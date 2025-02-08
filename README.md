# Brain Beaver :beaver:
  
## What is this?
  
- 마크다운 파일들을 대신 읽어 주요 내용을 요약하고 키워드를 추출합니다.
- `연두색 ~ 초록색` : 임베딩/벡터유사도를 기반으로 서로 연관된 것들을 연결하고 그래프 형태로 시각화합니다.
- `빨간색` : 웹에서 검색했을 때 반대되는 의견이 있으면 그래프로 연결해서 보여줍니다.
  
![](demo_001.png)
그림1 : 노드를 선택하면 세부내용을 볼 수 있다.
  
![](demo_002.png)
그림2 : 빨간색 노드는 웹으로 검색했을 때 잘못됐을 가능성이 높은 지식이다.
  
  
  
## Getting Started
  
- DB와 관련 컨테이너를 빌드하고 기동한다.
```bash
cd bb_docker
sudo docker compose build
docker compose up
```
  
- 파이썬 의존성을 설치
```bash
cd bb_src/Python.FastApi
python -m venv .venv
. .venv/bin/activate
pip install -r python/requirements
```

- 파이썬 앱 기동
```
cd bb_src/Python.FastApi
python app.py
```
  
- 그외 설정사항
  - 마크다운 데이터 경로, 모델 종류 등은 `app.py`에서 설정
  - OpenAI, Naver 검색 키 등은 `config.properties`, `secret.properties`에서 설정
  - `secret.properties`는 `secret.sample.properties`을 참고해 작성
  - `Python 3.12`, `Mac M1`에서 작업함. `Python 3.13`에서 일부 의존성 충돌 있음
  - Debian OS는 `psycopg2` 대신 apt 등으로 `psycopg2-binary` 패키지 설치 필요
