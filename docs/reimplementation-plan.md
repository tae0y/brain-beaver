# 브레인비버 재구현 계획 (TO-BE 설계 가이드)

본 문서는 기존(AS-IS) 레포지토리 구조, 제공된 OpenAPI 사양, PRD 초안, UI AS-IS 문서를 바탕으로 향후 재구현(리팩터링 & 확장) 시 코드 어시스턴트가 일관되고 안전하게 작업할 수 있도록 하는 상세 실행 지침을 제공한다. **핵심 목표**는 (1) Dev/Prod 환경 분리, (2) 파일/웹 파이프라인 증분 & 재시작 처리, (3) 병렬 처리 설정화, (4) 관측성/배포 자동화를 확보하는 것이다.

---

## 1. 배경 / 문제 요약

| 구분 | AS-IS | 한계 | TO-BE 방향 |
|------|-------|------|-------------|
| 프로젝트 구조 | 단일 FastAPI + 일부 디렉터리(`concepts/`, `networks/` 등) | 파이프라인/잡/증분 기능 부족, 책임 분리 미흡 | 도메인/파이프라인/인프라 계층화, 워커 분리 |
| 처리 방식 | 일괄 처리 (추정) | 대용량 시 장시간(2박3일), 중단 재개 불가 | 해시 기반 증분 + 단계별 상태 저장 |
| 병렬성 | 고정/내장 | 스케일 튜닝 곤란 | 설정파일/ENV 기반 런타임 조정 |
| 관측성 | 제한 (엔드포인트 일부) | 진행률/실패율/큐 지표 부재 | Prometheus Metrics + /jobs API + 구조화 로그 |
| 배포 | 단일 Docker (Dev/Prod 구분 약함) | 개발/운영 차이 반영 어려움 | 멀티스테이지 / dev vs prod compose / 로컬 레지스트리 |
| 확장성 | 특정 데이터 타입 중심 | 웹 크롤링/증분 전처리 미구현 | 파일·웹 소스 모두 파이프라인화 |

---

## 2. 기능 범위 (Functional Scope)

### 2.1 유지 & 정비할 기존 도메인 (OpenAPI 기반)
- Concepts CRUD (`/api/concepts`, `/api/concepts/{id}`, `/api/concepts/{id}/source-target-count`, `/api/concepts/count`)
- Networks 연결/조회/삭제 (`/api/networks`, `/api/networks/engage`)
- References 조회/삭제/확장 (`/api/references`, `/api/references/expand`)
- Extract 추출/예산 산정 (`/api/extract`, `/api/extract/check-budget`)

### 2.2 신규/확장 필요 기능
| 기능 | 신규 엔드포인트(안) | 요약 |
|------|--------------------|------|
| 폴더 스캔 | `POST /folders/scan` | 파일 메타/해시 upsert, documents 테이블 생성/업데이트, Job 발급 |
| 폴더 처리 | `POST /folders/process` | 스캔된 문서 중 미처리/변경 대상 파이프라인 실행 (resume/overwrite 옵션) |
| 웹 크롤 시작 | `POST /crawl/start` | URL BFS/깊이/허용도메인/레이트 설정 포함 Job 생성 |
| 잡 목록/조회 | `GET /jobs`, `GET /jobs/{id}` | 상태, 진행률, 실패 상세 |
| 헬스체크 | `GET /healthz`, `GET /readyz` | Liveness / Readiness 구분 |
| 메트릭 | `GET /metrics` | Prometheus 포맷 |
| 설정 조회(선택) | `GET /config` | 런타임 병렬/모델/크롤 파라미터 출력 (보안정보 제외) |
| 네임스페이스 리셋(관리) | `POST /admin/reset` | 개발 편의: 일부/전체 테이블 초기화(Dev Only) |

### 2.3 파이프라인 단계 정의 (파일 & 웹 공유 코어)
1. 수집(Source Load) – 파일 시스템 / HTTP 크롤
2. 정규화(Normalize) – 포맷 통일, 메타 추출(frontmatter, title)
3. 분절(Chunking) – 토큰/문단/헤딩 기준, 구성 가능한 최대 토큰
4. 요약(Summarize) – LLM 또는 로컬 모델 (배치/동시성 고려)
5. 검증(Validate) – 길이, 언어, 금칙어, 빈청크 제거
6. 임베딩(Embed) – 배치 처리, 모델 프로바이더 추상화
7. 링크(Linking) – 내부 역링크 + 벡터 유사도 기반 세맨틱 링크 생성
8. 그래프 Upsert – 노드/엣지/카운트 집계 반영
9. 상태 Commit – 각 단계 성공/실패 기록, 부분 재실행 지원

---

## 3. 비기능 요구 (Non-Functional)
- 성능: 대용량 처리시간 50%+ 단축 (파이프라인 병렬화 + 증분 스킵률 향상)
- 확장성: 워커 수/배치 크기 설정화, Postgres 기반 큐 → 후속 MQ 교체 용이 어댑터 패턴
- 안정성: 단계별 idempotent upsert, 재시도(지수 백오프), 부분 실패 격리
- 관측성: 레이턴시(p50/p95), Throughput(doc/s, chunk/s), 진행률 %, 실패 카운트, 큐 길이
- 보안: API 키(.env/secret) 분리, CORS/Rate Limit 옵션화, Prod 읽기전용 파일시스템
- 신뢰성: Graceful Shutdown(작업 재큐잉), Dead Letter 큐(실패 N회 초과)
- 테스트성: 해시/증분 로직 순수 함수화, 파이프라인 단계 단위 테스트 가능 구조

---

## 4. 기술 스택 / 라이브러리 선정

| 계층 | 선택 | 비고 |
|------|------|------|
| API 프레임워크 | FastAPI | 기존 유지, Pydantic v2 사용 권장 |
| 워커 실행 | Async + 멀티프로세스 혼합 | I/O (크롤/LLM) async, CPU (파싱/토큰화) process pool |
| DB | PostgreSQL + (선택) pgvector | 임베딩 저장/유사도 검색; 초기엔 테이블 + cosine 계산도 가능 |
| 큐 | Postgres LISTEN/NOTIFY → Adapter | scale 필요시 Redis/RabbitMQ 교체 쉽게 추상화 |
| 크롤러 | httpx + selectolax/BeautifulSoup + robots.txt | rate limit / retry / cache |
| 토큰화 | tiktoken(or transformers) | 모델별 토큰 카운트 |
| 임베딩 | OpenAI / Ollama / Local (pluggable) | 전략 패턴 provider.* 모듈 |
| 요약 | 동일 LLM provider | 모델 이름 구성화 |
| 설정 | pydantic Settings + configparser 병합 | ENV 우선, ini fallback |
| 관측성 | Prometheus client, structlog/loguru | json 로그 + metrics |
| 테스트 | pytest + factory | 임베딩/LLM mocking |
| 도커 | Multi-stage + buildx | dev/prod 분리, 로컬 레지스트리 push |
| 프론트 | Vite + TS (기존) | /jobs 진행률 패널 컴포넌트 추가 |

---

## 5. AS-IS 구조 분석 요약
현재 `src/Python.FastAPI` 하위에 `concepts/`, `networks/`, `references/`, `extract/`, `common/` 등 단순 디렉터리. 파이프라인/잡/증분/크롤에 해당하는 계층 부재.

문제점:
- 라우터/서비스/리포지토리 구분 불명확
- 데이터 모델(문서/청크/잡 등) 스키마 미정 → 확장 시 마이그레이션 리스크
- 재사용 가능한 인프라(설정 로더, DB 세션, 큐 인터페이스) 분리 필요

---

## 6. 제안 TO-BE Python 패키지 레이아웃

```
Python.FastAPI/
  app.py (엔트리, 라우터 include)
  core/
    config.py         # Settings 로딩 (env + ini)
    db.py             # 세션, 초기화
    logging.py        # 로거/구조화
    events.py         # startup/shutdown hooks
  domain/
    concepts/...
    networks/...
    references/...
    extract/...
    documents/        # 신규 (파일/웹 공통 Document)
    jobs/             # Job 엔티티 + 상태 머신
  pipeline/
    steps/            # normalize/chunk/... 각 단계 모듈
    file_scanner.py
    file_processor.py
    web_crawler.py
    orchestrator.py   # Job 디스패치, 큐 listen
    adapters/
      queue_postgres.py
      queue_interface.py
      embedding_openai.py
      embedding_ollama.py
      summarizer_openai.py
  api/
    routers/          # FastAPI APIRouter 세분화
      concepts.py
      networks.py
      references.py
      extract.py
      folders.py      # scan/process
      crawl.py
      jobs.py
      health.py
      metrics.py
  schemas/            # Pydantic DTO
  migrations/         # Alembic
  tests/
    unit/
    integration/
```

특징:
- `domain/` 은 비즈니스 규칙(엔티티/리포지토리) 중심.
- `pipeline/steps` 는 순수 처리 로직을 함수/클래스로 구성 (의존성 주입 기반). Mock 용이.
- `adapters/` 는 외부 시스템(LLM, 큐, 임베딩, 크롤) 추상화.
- `api/routers` 는 경량 Thin Layer, 서비스/도메인 호출.

---

## 7. 데이터 모델 & 마이그레이션 (초안)

```sql
-- documents
id BIGSERIAL PK
source_type TEXT CHECK (source_type IN ('file','web'))
uri TEXT UNIQUE -- 파일 path 또는 URL 식별자
path TEXT NULL, url TEXT NULL
mtime TIMESTAMPTZ NULL
size BIGINT NULL
content_hash CHAR(64) NOT NULL
title TEXT, meta JSONB
status TEXT CHECK (status IN ('pending','processed','failed')) DEFAULT 'pending'
created_at TIMESTAMPTZ DEFAULT now()
updated_at TIMESTAMPTZ DEFAULT now()

-- chunks
id BIGSERIAL PK
document_id BIGINT REFERENCES documents(id) ON DELETE CASCADE
ordinal INT
text TEXT
token_len INT
hash CHAR(64)
UNIQUE(document_id, ordinal)

-- summaries
id BIGSERIAL PK
document_id BIGINT REFERENCES documents(id) ON DELETE CASCADE
chunk_id BIGINT NULL REFERENCES chunks(id) ON DELETE CASCADE
model TEXT
text TEXT

-- embeddings (pgvector 사용 시 vector 컬럼)
id BIGSERIAL PK
chunk_id BIGINT REFERENCES chunks(id) ON DELETE CASCADE
provider TEXT
dim INT
vector VECTOR(1536)  -- 옵션: pgvector 설치 전엔 별도 table/JSON 저장

-- links
id BIGSERIAL PK
src_chunk_id BIGINT REFERENCES chunks(id) ON DELETE CASCADE
dst_chunk_id BIGINT REFERENCES chunks(id) ON DELETE CASCADE
score REAL
link_type TEXT CHECK (link_type IN ('explicit','semantic'))
UNIQUE(src_chunk_id, dst_chunk_id, link_type)

-- jobs
id BIGSERIAL PK
kind TEXT CHECK (kind IN ('scan','process','crawl'))
params JSONB
state TEXT CHECK (state IN ('queued','running','succeeded','failed','canceled'))
progress REAL DEFAULT 0
total INT DEFAULT 0
succeeded INT DEFAULT 0
failed INT DEFAULT 0
started_at TIMESTAMPTZ NULL
finished_at TIMESTAMPTZ NULL
error TEXT NULL

-- url_cache (웹 크롤 incremental)
url TEXT PRIMARY KEY
url_hash CHAR(64) NOT NULL
etag TEXT NULL
last_modified TEXT NULL
fetched_at TIMESTAMPTZ
status_code INT
content_hash CHAR(64)
```

마이그레이션 전략:
1. Alembic 초기 revision 생성 → 위 스키마 반영
2. pgvector 확장 여부 플래그 (`ENABLE_PGVECTOR`) 로 조건부 실행 (DDL: `CREATE EXTENSION IF NOT EXISTS vector;`)
3. 향후 link scoring 추가 컬럼(score_secondary 등) 시 마이그레이션 스크립트 분리

---

## 8. 파이프라인 증분 처리 설계

### 8.1 파일 스캔 알고리즘
```python
def scan(root):
  for file in glob_md_files(root):
    st = os.stat(file)
    h = sha256_read(file)
    upsert_document(uri=file, path=file, mtime=st.mtime, size=st.st_size, content_hash=h)
  mark_deleted_docs(root)  # 더 이상 존재하지 않는 path 상태 갱신(optional)
```

증분 처리 판단: `existing.content_hash != new_hash` → 상태 `pending` 리셋, 아니면 `skip`.

### 8.2 웹 크롤 증분
1. URL 정규화 → hash
2. url_cache 조회 → ETag/Last-Modified 비교 (조건부 GET 사용 가능)
3. 변경 없으면 skip, 변경 시 fetch & 파이프라인 큐잉

### 8.3 단계 상태 관리
- 기본 정책: 문서 단위 작업 실패 시 해당 문서만 재시도 큐에 push
- Job progress = (processed_or_skipped_docs / total_docs)
- 실패 재시도: exponential backoff (2^attempt * base) ≤ MAX_DELAY

---

## 9. 잡 & 워커 오케스트레이션

| 요소 | 설계 요약 |
|------|-----------|
| Job Queue | Postgres jobs.state = 'queued' → 워커 poll (LISTEN/NOTIFY) |
| 워커 동시성 | 프로세스 N (PARALLEL_WORKERS) + 내부 async task pool (BATCH_SIZE) |
| 취소 | jobs.state='canceled' 플래그 시 워커 graceful abort (현재 청크 완료 후 중단) |
| 재시작 | 재기동 시 'running' → 'queued'(recover) 로 전환 후 재할당 |
| Dead Letter | 실패 횟수 > RETRY_MAX → jobs.error 기록, state='failed' |

간단 Pseudo:
```python
while True:
  job = fetch_next_job()
  if not job: wait()
  process_job(job)
```

---

## 10. 설정 관리

우선순위: ENV > config.dev.ini|config.prod.ini > defaults.

예시 구조:
```ini
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
Pydantic Settings 로 읽고, 값 검증 (min/max) 수행.

---

## 11. 관측성 & 메트릭

Prometheus Export 예시:
| 메트릭 | 타입 | 라벨 | 설명 |
|--------|------|------|------|
| brainbeaver_documents_total | Counter | source_type | 처리된 문서 수 |
| brainbeaver_chunks_total | Counter |  | 생성된 청크 수 |
| brainbeaver_job_duration_seconds | Histogram | kind | Job 처리 시간 |
| brainbeaver_step_duration_seconds | Histogram | step | 파이프라인 단계별 지연 |
| brainbeaver_failures_total | Counter | step,error_type | 실패 카운트 |
| brainbeaver_queue_depth | Gauge | kind | 대기 Job 수 |
| brainbeaver_inflight_tasks | Gauge | step | 현재 실행 중 태스크 |
| brainbeaver_rate_limit_sleep_seconds | Counter | domain | 크롤 지연 누적 |

로그: JSON 구조 (timestamp, level, job_id, doc_id, step, message, latency_ms, attempt).

---

## 12. 도커 & 배포 전략

### 12.1 Dev
- `docker-compose.dev.yml` : api/ui/worker 소스 볼륨 마운트, uvicorn --reload, Vite dev server
- pg / pgadmin / portainer / registry / grafana / loki / tempo / otelcollector (이미 repo에 유사 구성 존재) 연동 검토

### 12.2 Prod
- Multi-stage Dockerfile (builder → slim runtime)
- 이미지 태그: `registry.local:5000/brain-beaver/{api,worker,ui}:<gitsha>`
- 읽기전용 루트 FS, non-root user, healthcheck 스크립트
- `.env.prod` 은 비밀 제외, 비밀은 runtime 주입(secrets)

### 12.3 배포 파이프라인
1. 테스트 & 린트 → 2. 빌드 이미지(buildx) → 3. 로컬 레지스트리 push → 4. compose.prod up -d
2. 옵션: Git hook 또는 Makefile (`make deploy`) 정의

---

## 13. 테스트 전략

| 레벨 | 대상 | 예시 |
|------|------|------|
| 단위(Unit) | 해시/증분, chunk 분할, 링크 스코어 | hash unchanged skip, large doc splitting |
| 서비스 | file_scanner → documents upsert | mock fs, temp files |
| 파이프라인 | End-to-end 소량 문서 → summaries/embeddings 생성 | provider mock |
| 크롤러 | robots/redirect/rate limit | httpx mock server |
| DB 마이그 | Alembic upgrade/downgrade idempotent | ephemeral DB |
| 성능(벤치) | 1k docs / 100 pages | 처리시간, p95 단계 지연 |

CI 시 빠른 subset, 주기적(또는 수동)으로 벤치 프로파일.

---

## 14. 단계별 구현 로드맵 (우선순위)
1. 스키마 & Alembic 초기화 (documents/chunks/jobs ...)
2. 설정 로더(core.config) + 로깅(core.logging)
3. 파일 스캐너(scan) + /folders/scan API + Job 저장
4. 파일 파이프라인(process) + /folders/process API
5. 잡 오케스트레이터/워커(큐 인터페이스, LISTEN/NOTIFY)
6. 웹 크롤러 + /crawl/start API + url_cache
7. 요약/임베딩 provider 추상화 + 배치 처리
8. 링크 생성 알고리즘(벡터 유사도 + 역링크) & networks 반영
9. /jobs, /metrics, /healthz, /readyz
10. 관측성(Grafana 대시보드 예시 JSON) & 구조화 로그
11. Dev/Prod Docker & compose 분리 + 레지스트리 Push 스크립트
12. 성능 튜닝(멀티프로세스, 배치 크기 동적) & 테스트 확장

병렬 진행 가능: (A) 스키마+설정, (B) 스캐너, (C) 워커, (D) LLM Provider / 임베딩.

---

## 15. 위험요소 & 완화 전략
| 위험 | 설명 | 완화 |
|------|------|------|
| LLM API 지연/한도 | 임베딩/요약 호출 대기 | 배치 + 동시요청 제한 + 캐시(hash→임베딩) |
| 대용량 메모리 | 대형 문서 전체 로드 | 스트림 읽기 + 청크 단위 처리 |
| 크롤 루프 | 무한 링크 확장 | depth, domain allowlist, 방문 집합, 페이지 한도 |
| 중단 시 일관성 | 프로세스 crash | 단계별 커밋 + running→queued 복구 |
| pgvector 미설치 | 초기 환경 제약 | feature flag로 fallback(JSON 저장) |
| 잠금 경합 | 대량 upsert | UPSERT 배치, COPY 활용(추후), 인덱스 최소화 초기설계 |

---

## 16. 구현 시 코딩 어시스턴트 지침
1. 새로운 모듈 추가 전 해당 책임 범위(도메인/파이프라인/어댑터) 명확히 구분.
2. 외부 의존성 추가 시: requirements 파일(`py.conf/requirements.txt`) 업데이트 & 최소 버전 명시.
3. 퍼블릭 함수/클래스 docstring: 입력/출력/예외/Idempotency 명시.
4. 파이프라인 단계 함수는 순수 함수 선호, I/O/DB는 단일 어댑터 계층.
5. 재시도 로직은 공통 데코레이터(@retryable)로 구현.
6. 메트릭/로그는 단계 시작/종료/실패에 최소 1회 기록.
7. 테스트 작성 순서: (a) 증분 해시, (b) 청크 분할, (c) Job state 전이, (d) 크롤 중복 제거.
8. 마이그레이션 스크립트 변경 시 README (또는 MIGRATIONS.md)에 수동 수행 지침 업데이트.
9. 성능 민감 코드(임베딩 배치)는 상수/매직 넘버 하드코딩 금지 → 설정 의존.
10. 모든 새 API는 OpenAPI description/response 모델 정의 후 구현.

---

## 17. 예시: 파이프라인 단계 인터페이스 (코드 스니펫)
```python
class PipelineContext(BaseModel):
    document_id: int
    source_type: str
    text: str
    metadata: dict = {}

class Step(Protocol):
    name: str
    def run(self, ctx: PipelineContext) -> PipelineContext: ...

class ChunkStep:
    name = "chunk"
    def __init__(self, tokenizer, max_tokens: int):
        self.tokenizer = tokenizer
        self.max_tokens = max_tokens
    def run(self, ctx: PipelineContext):
        # 분절 로직 -> DB insert (chunks)
        return ctx
```

---

## 18. 향후 확장 고려
- Knowledge Graph 시각화 API (노드/에지 페이징, 필터)
- Elastic / OpenSearch 인덱싱 (검색 성능)
- Embedding 벡터 외 Sparse Hybrid (BM25 + Vector)
- 모델 프로바이더 다중 Failover (OpenAI→로컬)
- 스케줄러(APScheduler) 통한 주기적 재스캔/크롤

---

## 19. 완료 정의 (Definition of Done)
| 항목 | 기준 |
|------|------|
| 증분 처리 | 변경 없는 파일 2회 처리 시 second pass 90% 이상 SKIP |
| 재시작 복구 | 강제 종료 후 1분 내 running→queued 재할당 |
| 메트릭 | 명세된 70% 이상 노출 & Grafana 대시 예시 | 
| 성능 | 벤치 데이터 기준 50% 이상 속도 개선 또는 로그/지표 근거 보고 |
| 테스트 | 단위/통합 커버리지 핵심 로직(증분/잡/크롤/청크) > 70% |
| 보안/비밀 | API 키 코드 하드코딩 금지 (grep 검사) |

---

## 20. 요약
본 계획은 기존 OpenAPI 기반 CRUD 도메인을 유지하면서 **증분형 파이프라인**, **잡/워커 오케스트레이션**, **관측성과 Dev/Prod 분리 배포**를 도입하여 확장성과 운영성을 개선한다. 문서 구조 / 단계적 로드맵 / 데이터 모델 / 메트릭 정의를 통해 코드 어시스턴트가 체계적으로 구현을 진행할 수 있는 내용으로 구성하였다.

> 다음 단계 제안: (1) Alembic 초기 마이그레이션 스크립트 생성, (2) core.config / core.db / core.logging 작성, (3) 파일 스캐너 최소 구현 & 단위 테스트 작성.
