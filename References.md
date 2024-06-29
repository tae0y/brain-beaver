# References
> 참고한 기술문서 목록

## Jupyter

- jupyter notebook
```shell
pip isntall jupyter #가상환경 내부에서 주피터를 설치
jupyter notebook #주피터 구동
#인터페이스는 vscode를 추천
```


## Ollama
- ollama api 문서
https://github.com/ollama/ollama/blob/main/docs/api.md

- m1 터미널에서 GPU 모니터링, ANE은 사용할 수 없음
https://github.com/tlkh/asitop


## Sqlalchemy for PostgreSQL/Pgvector
- https://learn.microsoft.com/en-us/samples/azure-samples/azure-postgres-pgvector-python/azure-postgres-pgvector-python/
- https://github.com/pgvector/pgvector-python/tree/master
- https://medium.com/naver-shopping-dev/streamlit-interactive-graph-network-visualization-e5775908da94


## Docker 구동방법

- 도커이미지 : https://hub.docker.com/r/ubuntu/postgres
- pgvector : https://github.com/pgvector/pgvector?tab=readme-ov-file#apt
  - 트러블슈팅 https://stackoverflow.com/questions/56724622/how-to-fix-postgres-h-file-not-found-problem

- `docker-compose.yml` 디렉토리에서 명령어를 실행한다.
- 도커를 켜기만 할 때는
```shell
docker compose up   #구동
docker compose down #삭제
```

- 도커파일 등을 수정해서 새로 빌드해야할 때는
```shell
docker-compose build --no-cache
docker-compose up -d 
```

- pgadmin에 pgdatabase를 연결할 때는
  - pgadmin은 `localhost:5050`처럼 로컬호스트로 접속한다.
  - pgadmin에서 db에 접속할때는 아래 명령어로 IP를 확인한다.
  - 192.168.227.2 / 192.168.117.2
```shell
docker ps | grep bwsdb_container | awk '{print $1}'
docker inspect af84 | grep IPAddress
```

- init.d를 수정했을 때는
```shell
docker compose down
docker volume prune
docker compose up
```

- 도커의 모든 이미지를 삭제
```shell
docker rmi $(docker images -q) #도커이미지 완전삭제
```


