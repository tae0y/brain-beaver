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
  
### With Aspire/AppHost
- 파이썬 의존성을 설치
```bash
cd src/Python.FastApi
python -m venv .venv
. .venv/bin/activate
pip install -r python/requirements
```

- AppHost를 통해 도커 및 파이썬 기동
```bash
# 개발용 SSL
cd src/Aspire.AppHost
dotnet dev-certs https --clean && dotnet dev-certs https --trust

# 도커 권한설정 (아래 명령어 실행후 도커데몬 재시작)
sudo chown -R $USER ~/.docker
sudo chmod -R 775 ~/.docker

# AppHost 기동
cd src/Aspire.AppHost
dotnet run --project Aspire.AppHost.csproj

# Opentelemetry + Uvicorn + FastAPI 기동 (AppHost 9.2부터 Opentelemetry/Uvicorn 지원예정)
OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:18888 \
OTEL_EXPORTER_OTLP_TRACES_ENDPOINT=http://localhost:18888/v1/traces \
OTEL_EXPORTER_OTLP_METRICS_ENDPOINT=http://localhost:18888/v1/metrics \
OTEL_EXPORTER_OTLP_LOGS_ENDPOINT=http://localhost:18888/v1/logs \
opentelemetry-instrument \
  --traces_exporter otlp \
  --metrics_exporter otlp \
  --logs_exporter otlp \
  uvicorn app:app

opentelemetry-instrument --traces_exporter otlp --logs_exporter console,otlp --metrics_exporter otlp uvicorn app:app 
```

### Without Aspire/AppHost
- DB와 관련 컨테이너를 빌드하고 기동한다.
```bash
cd docker
sudo docker compose build
docker compose up
```
  
- 파이썬 의존성을 설치
```bash
cd src/Python.FastApi
python -m venv .venv
. .venv/bin/activate
pip install -r python/requirements
```

- 파이썬 앱 기동
```bash
# Opentelemetry + Uvicorn + FastAPI 기동
cd src/Python.FastApi
opentelemetry-instrument --traces_exporter otlp --logs_exporter console,otlp --metrics_exporter otlp uvicorn app:app
```


### Notice
- 그외 설정사항
  - 마크다운 데이터 경로, 모델 종류 등은 `app.py`에서 설정
  - OpenAI, Naver 검색 키 등은 `config.properties`, `secret.properties`에서 설정
  - `secret.properties`는 `secret.sample.properties`을 참고해 작성
  - `Python 3.12`, `Mac M1`에서 작업함. `Python 3.13`에서 일부 의존성 충돌 있음
  - Debian OS는 `psycopg2` 대신 apt 등으로 `psycopg2-binary` 패키지 설치 필요


## 앱 구조
- `Dotnet.BlazorUI` : 데이터소스를 입력해 데이터추출, 예상비용 확인, 결제 및 진행
- `Java.SpringBFF` : extract, engage, expand 기능 단위로 여러 API를 묶어서 호출
- `Python.FastAPI` : concepts, networks, references 도메인 기반 단편화된 API 제공
- `Docker` : portainer, postgresql, pgadmin 컨테이너
- `Aspire.AppHost` : 상기 모든 앱과 도커 컨테이너를 호스팅, 대시보드/모니터링/장애회복 기능제공
- `Aspire.ServiceDefaults` : 클라우드 네이티브 앱 호스팅 기본값 설정