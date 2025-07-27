# DB 설정방법

docker build -t bws_db -f Dockerfile-bwsdb .

docker run --name bitnami-prime \
  -e POSTGRESQL_REPLICATION_MODE=master \
  -e POSTGRESQL_REPLICATION_USER="u_repl" \
  -e POSTGRESQL_REPLICATION_PASSWORD="1!(u_repl)" \
  -e POSTGRES_USER=root \
  -e POSTGRES_PASSWORD=root \
  -e POSTGRES_DB=bwsdb \
  -p 5432:5432 \
  -d bws_db