# Brain Beaver :beaver:
  
## 개요
  
- 마크다운 파일을 대신 읽고, 연관관계를 `별자리`처럼 표현합니다.
![](./demo_001.png)

- 파란색, 하늘색, 분홍색의 각 노드를 클릭하면 세부정보를 볼 수 있습니다.
![](./demo_002.png)  
  
## 시작하기

- docker
```bash
# docker compose, build
cd docker
docker compose up --build
```

- docker swarm
```bash
# docker build
cd docker
docker build -t bws_container_admin -f Dockerfile-dockeradmin .
docker build -t bws_db -f Dockerfile-bwsdb .
docker build -t bws_db_admin -f Dockerfile-bwsdbadmin .
docker build -t bws_db_bwsmq -f Dockerfile-bwsmq .
docker build -t bws_backend -f Dockerfile-pythonfastapi .
docker build -t bws_vite -f Dockerfile-bwsvite .
docker build -t bws_backup -f Dockerfile-backup .

# docker stack
sudo docker stack deploy -c docker-swarm-compose.yml bws_stack --detach=false
```

  
## 앱의 구조
- FrontEnd : Node ViteUI
- BackEnd : Python FastAPI
  - API 문서는 `/swagger`에서 확인
  - 마크다운 데이터 경로, 모델 종류 등은 `app.py`에서 설정
  - OpenAI, Naver 검색 키 등은 `config.properties`, `secret.properties`에서 설정
  - `secret.properties`는 `secret.sample.properties`을 참고해 작성
  - `Python 3.12`, `Mac M1`에서 작업함. `Python 3.13`에서 일부 의존성 충돌 있음
  - Debian OS는 `psycopg2` 대신 apt 등으로 `psycopg2-binary` 패키지 설치 필요
- MessqgeQueue : RabbitMQ
- DataBase : PostgeSql, PgAdmin
- DevOps : Portainer, Grafana/Loki/Tempo, Jenkins
- 그외(계획중) : Spring Batch, NestJS BFF, Aspire ServiceDefaults