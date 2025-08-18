# BrainBeaver Docker 구성 가이드

이 디렉토리는 BrainBeaver 프로젝트의 Docker 컨테이너 구성을 포함합니다.
개발용과 운영용 환경을 분리하여 제공합니다.

## 📁 디렉토리 구조

```
docker/
├── docker-compose.dev.yml      # 개발용 Docker Compose
├── docker-compose.prod.yml     # 운영용 Docker Compose  
├── docker-compose.yml          # 기본 링크 (개발용)
├── build-prod.sh               # 운영용 이미지 빌드 스크립트
├── Dockerfile-pythonfastapi    # 개발용 Python 백엔드
├── Dockerfile-pythonfastapi-prod # 운영용 Python 백엔드
├── Dockerfile-bwsvite          # 개발용 Vite 프런트엔드
├── Dockerfile-bwsvite-prod     # 운영용 Vite 프런트엔드
└── ... (기타 서비스 Dockerfile들)
```

## 🚀 개발 환경

### 특징
- **소스 파일 볼륨 마운트**: 코드 변경사항이 실시간 반영
- **Hot Reload**: 자동 재로드로 빠른 개발 피드백
- **의존성만 설치**: 빌드 시 패키지만 설치하고 소스는 볼륨 마운트

### 시작하기

```bash
cd docker
docker-compose -f docker-compose.dev.yml up -d

# 또는 기본 docker-compose.yml 사용 (개발용으로 링크됨)
docker-compose up -d
```

### 접속 주소
- **UI**: http://localhost:5173
- **Backend API**: http://localhost:8112/docs
- **DB Admin**: http://localhost:5050
- **Docker Admin**: http://localhost:9000
- **Backup Scheduler**: http://localhost:8080

### 개발 중 재시작
```bash
# 특정 서비스만 재시작
docker-compose restart bws_backend
docker-compose restart bws_vite

# 전체 재시작
docker-compose down && docker-compose up -d
```

## 🏭 운영 환경

### 특징
- **소스 코드 포함**: 빌드 시 소스 파일을 이미지에 포함
- **재현 가능한 환경**: 모든 코드가 이미지에 포함되어 일관된 배포
- **로컬 레지스트리**: 빌드된 이미지를 로컬 레지스트리에 등록

### 이미지 빌드 및 레지스트리 등록

```bash
cd docker

# 기본 설정으로 빌드 (localhost:5000 레지스트리)
./build-prod.sh

# 커스텀 설정으로 빌드
BUILD_TAG=v1.0.0 REGISTRY_HOST=my-registry:5000 ./build-prod.sh
```

### 운영 환경 시작

```bash
# 운영용 컨테이너 실행
docker-compose -f docker-compose.prod.yml up -d

# 이미지가 로컬에 없으면 레지스트리에서 자동 다운로드
docker-compose -f docker-compose.prod.yml pull
docker-compose -f docker-compose.prod.yml up -d
```

### 운영 환경 관리

```bash
# 상태 확인
docker-compose -f docker-compose.prod.yml ps

# 로그 확인
docker-compose -f docker-compose.prod.yml logs -f

# 중지
docker-compose -f docker-compose.prod.yml down

# 완전 삭제 (볼륨 포함)
docker-compose -f docker-compose.prod.yml down -v
```

## 🔧 고급 설정

### 로컬 레지스트리 수동 설정

```bash
# 로컬 레지스트리 시작
docker run -d -p 5000:5000 --restart=always --name registry registry:2

# 레지스트리 확인
curl http://localhost:5000/v2/_catalog
```

### 개별 이미지 빌드

```bash
# 백엔드만 빌드
docker build -f Dockerfile-pythonfastapi-prod -t localhost:5000/brain-beaver/backend:latest ..

# 프런트엔드만 빌드  
docker build -f Dockerfile-bwsvite-prod -t localhost:5000/brain-beaver/frontend:latest ..

# 이미지 푸시
docker push localhost:5000/brain-beaver/backend:latest
docker push localhost:5000/brain-beaver/frontend:latest
```

### 환경별 설정 변경

#### 개발 환경 설정
- `docker-compose.dev.yml` 수정
- 볼륨 마운트 경로 조정
- 환경 변수 추가

#### 운영 환경 설정
- `docker-compose.prod.yml` 수정  
- 이미지 태그 변경
- 리소스 제한 설정

## 🐛 문제 해결

### 자주 발생하는 문제

1. **포트 충돌**
   ```bash
   # 사용 중인 포트 확인
   docker-compose ps
   netstat -tulpn | grep :5173
   ```

2. **볼륨 마운트 문제**
   ```bash
   # 볼륨 권한 확인
   ls -la ../src/
   
   # 컨테이너 내부 확인
   docker-compose exec bws_backend ls -la /SRC
   ```

3. **이미지 빌드 실패**
   ```bash
   # 캐시 없이 빌드
   docker-compose build --no-cache
   
   # 개별 서비스 빌드
   docker-compose build bws_backend
   ```

4. **레지스트리 연결 문제**
   ```bash
   # 레지스트리 상태 확인
   docker ps | grep registry
   curl http://localhost:5000/v2/_catalog
   ```

### 로그 확인

```bash
# 전체 로그
docker-compose logs

# 특정 서비스 로그
docker-compose logs bws_backend
docker-compose logs -f bws_vite  # 실시간

# 에러 로그만
docker-compose logs | grep ERROR
```

## 📚 참고 자료

- [Docker Compose 공식 문서](https://docs.docker.com/compose/)
- [Docker Registry 가이드](https://docs.docker.com/registry/)
- [BrainBeaver 프로젝트 README](../README.md)

## 🤝 기여하기

Docker 구성 개선 사항이나 문제점을 발견하시면 이슈를 등록해 주세요.

- 새로운 서비스 추가
- 성능 최적화
- 보안 개선
- 문서 업데이트