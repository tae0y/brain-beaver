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
sudo docker compose build
docker compose up
```
  
- 파이썬 의존성을 설치하고 앱을 기동한다.
```bash
# 프로젝트 루트경로에서 - vscode python 환경을 편하게 사용하기 위함
python -m venv .venv
. .venv/bin/activate
pip install -r python/requirements

# 앱 구동은 python에서 - 일부 상대경로를 참조함
cd python
python app.py
```
  
- 마크다운 데이터 경로, 모델 종류 등은 `app.py`에서 설정한다.