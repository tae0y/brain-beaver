# 브레인비버 PRD (초안)

> 목적: 코드 어시스턴트(바이브코딩)에게 전달할 제품/기술 요구사항 문서. 현재 레포지토리 구조를 존중하면서 **개발/운영 도커 분리**, **마크다운/웹 크롤링 파이프라인의 재처리∙증분처리**, **병렬 처리 설정화**, **로컬 레지스트리 기반 배포**를 설계한다.

---

## 1. 배경 & 문제정의

- 브레인비버는 마크다운/웹문서를 분해·요약·검증·연결해 지식 네트워크를 구성하는 도구다.
- AS‑IS의 과제: 대용량(로컬 전체 파일) 처리 시 **2박 3일** 소요, 재시작/증분 처리 미흡, 개발과 운영 컨테이너가 동일 구성으로 빌드/배포 효율 저하.
- TO‑BE 목표: (1) Dev/Prod 도커 분리 및 로컬 레지스트리 배포, (2) 파일/웹 소스의 **증분·이어달리기 처리**, (3) **외부 설정 기반 병렬화**로 처리시간 단축, (4) 관측성/복구성 강화.

## 2. 범위(Scope)

- 포함: 파이프라인(파일/웹) 백엔드(FastAPI)·워크커, UI 연동을 위한 API, DB 스키마 보강, 도커·배포 파이프라인, 설정/비밀키 관리, 관측성.
- 제외: 신규 UI 대리설계, 모델 연구개발(프롬프트/파라미터 최적화는 파이프라인 훅 제공으로 대체).

## 3. 핵심 사용자 시나리오

1. **폴더 처리 재개**: 사용자가 마크다운 폴더 경로를 지정 → DB에서 각 파일의 처리여부/해시 비교 → 미처리/변경 파일만 작업 → 중단 후 재개 가능.
2. **웹 도메인 수집**: 시작 URL을 입력 → 동일 도메인(or 허용 도메인 목록) 링크를 BFS/DFS로 크롤 → HTML 정제 → 마크다운 파이프라인과 동일하게 분절·요약·검증·링킹.
3. **성능 튜닝**: `config.ini`(또는 `.env`)에서 동시 작업 수/배치 크기/큐 크기 조절 → 처리시간 단축 → 진행률/ETA 확인.
4. **운영 배포**: 개발용 컨테이너로 빠른 수정/리로드, 운영용 이미지는 소스 포함 단일 이미지로 빌드 → 로컬 레지스트리에 `brain-beaver/*` 네임스페이스로 push → compose(or swarm/k8s)로 배포.

## 4. 기능 요구사항 (Functional)

### 4.1 파일(마크다운) 파이프라인

- 입력: 루트 폴더 경로.
- 스캔: 확장자 필터(`.md`, `.mdx`, 옵션: `.txt`, `.rst`) & ignore 패턴(`.git`, `node_modules`, 바이터리 등).
- **증분 처리**: 파일별 `content_hash(SHA256)`와 `mtime`, `size` 저장. DB에 `documents` 테이블에 upsert. 변경 감지 조건: 해시 변경 또는 삭제/이동 감지.
- 처리 단계: (a) 문서 정규화(프론트매터, 메타 제거/보존 설정), (b) 청크 분절(토큰/문단), (c) 요약, (d) 품질검증(길이/언어/금칙어), (e) 임베딩/키워드, (f) 링크 생성(역링크/연관도 기반), (g) 그래프 upsert.
- **이어하기/재시도**: 작업단계별 상태 저장(`pending/running/success/failed/skipped`) 및 리트라이 정책(지수 백오프, 최대 N회). 부분성공 기록 후 재개.
- 산출물: `documents`, `chunks`, `summaries`, `links`, `embeddings`, `jobs` 테이블 업데이트.

### 4.2 웹 크롤링 파이프라인

- 입력: 시작 URL(필수), 크롤링 깊이/페이지 한도/허용 도메인/robots 정책.
- 수집: 사이트맵 우선, 없으면 링크 추출 → 큐잉(BFS 기본) → 중복 URL 제거(정규화) → **증분**: `url_hash`로 중복/변경 감지(`ETag/Last-Modified` 헤더 캐시).
- 전처리: HTML→텍스트 추출(메뉴/푸터/광고 제거), 코드블록/표 유지 옵션, canonical title/description/meta 저장.
- 파이프라인: 파일과 동일한 (분절→요약→검증→임베딩→링크) 단계 적용.
- 예외: 크롤 금지/에러코드/레이트리밋 존중, 도메인당 동시요청/지연 설정.

### 4.3 설정/튜닝 (`config.ini` 또는 `.env`)

- 공통: `PARALLEL_WORKERS`, `BATCH_SIZE`, `QUEUE_MAX`, `RETRY_MAX`, `TIMEOUT_SEC`, `RATE_LIMIT`, `ALLOWED_DOMAINS`, `CRAWL_DEPTH`, `MODEL_PROVIDER(OPENAI|OLLAMA)`, `EMBED_MODEL`, `NAVER_API_KEY`, `OPENAI_API_KEY`.
- Dev/Prod override: `config.dev.ini`, `config.prod.ini` 병행 로드(환경변수 우선).

### 4.4 관측성 & 운영

- 작업 단위(Job/Task) 진행률, 처리량(문서/초), 대기 큐 길이, 실패율, 평균/95p 지연시간, 재시도 수.
- API: `/jobs` 목록/필터, `/jobs/{id}` 상세, `/metrics`(Prometheus), `/healthz`, `/readyz`.
- UI: 간단한 대시보드(이미 존재 UI 좌측 패널에 진행률/ETA/취소 버튼 추가 훅 제공).

## 5. 비기능 요구사항 (Non‑Functional)

- 성능: 로컬 전체(기준 X GB, Y만 라인) 처리시간을 **50% 이상** 단축(목표: 2박3일 → ≤ 1일). 병렬 설정으로 선형에 준하는 스케일 기대.
- 안정성: 비정상 종료 후 재기동 시 **Idempotent**. 중복 DB 기록 금지, 동일 입력 재처리 시 동일 그래프 보장.
- 보안: API 키/비밀은 시크릿 파일/환경변수로 분리. CORS/RateLimit 옵션 제공.

## 6. 시스템 아키텍처 (TO‑BE)

- **서비스 구성**
  - `ui` (Vite/TS): 진행률/잡 관리 패널 연동.
  - `api` (FastAPI): 작업 제출/상태조회/설정 조회, 파일 스캐너/크롤러 시작점 제공.
  - `worker` (Python): 큐 소비자. 파일/웹 처리 파이프라인. 동시성(프로세스/스레드/async) 선택 가능.
  - `db` (PostgreSQL): 문서/청크/링크/잡 상태 저장. pgvector(옵션)로 임베딩.
  - `scheduler` (예: `cron` 또는 `APScheduler`): 주기 작업.
  - `registry` (Docker Registry): 운영 이미지 저장.
- **통신**: `api`→`worker`는 내장 큐(Redis/RabbitMQ 없이 우선: Postgres LISTEN/NOTIFY 또는 파일큐). 추후 MQ 옵션 플러그블.

## 7. 데이터 모델(초안)

- `documents(id, source_type{file,web}, uri, path, url, mtime, size, content_hash, title, meta, status, created_at, updated_at)`
- `chunks(id, document_id, ordinal, text, token_len, hash)`
- `summaries(id, document_id, chunk_id?, model, text)`
- `links(id, src_chunk_id, dst_chunk_id, score, link_type{explicit,semantic})`
- `embeddings(id, chunk_id, provider, dim, vector)`
- `jobs(id, kind{scan,process,crawl}, params, state, progress, total, succeeded, failed, started_at, finished_at, error)`
- `url_cache(url, url_hash, etag, last_modified, fetched_at, status_code, content_hash)`

## 8. API 설계(요점)

- `POST /folders/scan` {root, patterns?, ignore?} → job id
- `POST /folders/process` {root, resume\:true, overwrite?\:false}
- `POST /crawl/start` {start\_url, allowed\_domains?, depth?, max\_pages?, rate?}
- `GET /jobs` / `GET /jobs/{id}`
- `GET /metrics`(Prometheus), `GET /healthz`, `GET /readyz`

## 9. 파이프라인 세부 (의사코드)

```
scan(root):
  for file in glob:
    meta = stat(file)
    hash = sha256(file)
    upsert(documents, key=(path), values=[mtime, size, hash])

process(document):
  if unchanged(hash): return SKIP
  blocks = chunk(document.text, max_tokens)
  for b in blocks: summarize→validate→embed
  linker.update(document)
```

## 10. 도커/배포 전략

### 10.1 Dev(개발)

- 소스 **볼륨 마운트**: `api:/app`, `ui:/app`, `worker:/app`.
- 빠른 핫리로드: `uvicorn --reload`, Vite `--watch`.
- 개발용 compose: `docker-compose.dev.yml`.

### 10.2 Prod(운영)

- **소스 포함 빌드**: `multi-stage Dockerfile`(빌드 → 런타임 slim)
- 이미지 태깅: `brain-beaver/api:<gitsha>`, `ui:<gitsha>`, `worker:<gitsha>`
- 로컬 레지스트리: `registry.local:5000` 운영. `docker buildx build ... --push`.
- 운영용 compose: `docker-compose.prod.yml`(이미지 참조, 볼륨 최소화, 읽기전용 FS, ulimits, healthcheck).
- 시크릿: `secret.properties`는 dev만 볼륨 마운트, prod는 `ENV`/`docker secrets`.

## 11. 설정 파일 예시

```ini
# config.prod.ini
[runtime]
PARALLEL_WORKERS=8
BATCH_SIZE=16
QUEUE_MAX=2000
RETRY_MAX=3
TIMEOUT_SEC=30

[crawl]
DEPTH=2
RATE_LIMIT_PER_DOMAIN=2
DELAY_MS=300
ALLOWED_DOMAINS=example.com,docs.example.com

[llm]
PROVIDER=OLLAMA
EMBED_MODEL=text-embedding-3-large
```

## 12. 성능 전략

- I/O 바운드: 크롤/파일읽기 비동기화, CPU 바운드(파싱/토큰화) 멀티프로세스 분리.
- **배치 임베딩**: 임베딩 호출을 배치화(메모리 상한 기반 동적 배치).
- **캐시**: URL/문서 해시 캐시, 중복 제거.
- **스로틀링**: API 레이트 리밋, 백오프.

## 13. 실패/복구/일관성

- 트랜잭션: 문서/청크/링크 upsert는 동일 트랜잭션 묶음.
- 재시도: 네트워크/LLM 오류는 지수 백오프.
- 부분 실패 기록 후 재개 가능(`resume:true`).

## 14. 테스트/수용 기준

- 단위: 해시/증분 로직, 파싱/분절, 링크 생성 점검.
- 통합: 폴더 1천 파일, 크롤 100페이지 시 **성능 지표** 출력 및 목표 충족 확인.
- E2E: Dev→Prod 이미지 빌드, 로컬 레지스트리 푸시, compose로 기동까지 자동화.

### 체크리스트(수용 기준)

-

## 15. 작업 패키지(바이브코딩 태스크)

1. **DB 스키마 마이그레이션**: 위 표 정의대로 Alembic 스크립트.
2. **파일 스캐너 & 증분 로직** 모듈.
3. **웹 크롤러**(robots/레이트리밋/중복제거/증분) 모듈.
4. **파이프라인 오케스트레이터**: Job 큐, 워커 병렬 처리.
5. **API 엔드포인트**(jobs/folders/crawl/metrics/healthz).
6. **설정 로더**: `config.dev.ini`, `config.prod.ini`, 환경변수 머지.
7. **도커 분리/빌드 파이프라인**: dev/prod Compose, 멀티스테이지 Dockerfile, 로컬 레지스트리 푸시 스크립트.
8. **관측성**: Prometheus 지표, 로그 구조화.
9. **성능 튜닝**: 배치 임베딩, 멀티프로세스/스레드 구성 벤치.

## 16. 오픈 이슈/결정 필요사항

- 임베딩 저장: pgvector 도입 여부/대안(FAISS/SQLite) 선택.
- MQ 선택: 단일 노드에선 Postgres NOTIFY로 시작, 확장 시 Redis/RabbitMQ 전환?
- UI 변경 범위: 잡 관리 패널을 어디에/어떻게 노출할지.
- 모델/요약 비용: OpenAI vs Ollama 조합 기본값.

---

### 부록 A. Docker 구성안(예시)

- `docker-compose.dev.yml`
  - api/ui/worker: `build: .` + `volumes: ./src:/app`
  - db/pgadmin/portainer/scheduler/registry 포함
- `docker-compose.prod.yml`
  - api/ui/worker: `image: registry.local:5000/brain-beaver/*:<gitsha>`
  - 최소 볼륨, 읽기전용, healthcheck, restart 정책

### 부록 B. 마이그레이션 스크립트 템플릿

- `alembic revision --autogenerate -m "add incremental columns"`

### 부록 C. 성능 가이드

- 워커 수 = min(코어×2, I/O 대역) / 임베딩 배치 = 메모리 60% 한계

