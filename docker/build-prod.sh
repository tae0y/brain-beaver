#!/bin/bash

# BrainBeaver Production Build Script
# 이 스크립트는 운영용 Docker 이미지를 빌드하고 로컬 레지스트리에 등록합니다.

set -e  # 에러 발생시 스크립트 중단

# 색상 정의
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 로깅 함수
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 설정
REGISTRY_HOST="${REGISTRY_HOST:-localhost:5000}"
PROJECT_NAME="brain-beaver"
BUILD_TAG="${BUILD_TAG:-latest}"

# 이미지 목록 정의
declare -A IMAGES=(
    ["backend"]="../docker/Dockerfile-pythonfastapi-prod"
    ["frontend"]="../docker/Dockerfile-bwsvite-prod"
    ["container-admin"]="./Dockerfile-dockeradmin"
    ["db"]="./Dockerfile-bwsdb"
    ["db-admin"]="./Dockerfile-bwsdbadmin"
    ["mq"]="./Dockerfile-bwsmq"
    ["backup"]="./Dockerfile-backup"
)

# Docker가 실행 중인지 확인
check_docker() {
    log_info "Docker 실행 상태 확인 중..."
    if ! docker info >/dev/null 2>&1; then
        log_error "Docker가 실행 중이지 않습니다. Docker를 시작하고 다시 시도하세요."
        exit 1
    fi
    log_success "Docker가 실행 중입니다."
}

# 로컬 레지스트리 확인/시작
setup_local_registry() {
    log_info "로컬 레지스트리 확인 중..."
    
    if ! docker ps | grep -q "registry:2"; then
        log_warning "로컬 레지스트리가 실행 중이지 않습니다. 시작합니다..."
        docker run -d -p 5000:5000 --restart=always --name registry registry:2
        log_success "로컬 레지스트리를 시작했습니다."
    else
        log_success "로컬 레지스트리가 이미 실행 중입니다."
    fi
}

# 이미지 빌드
build_image() {
    local service=$1
    local dockerfile=$2
    local image_name="${REGISTRY_HOST}/${PROJECT_NAME}/${service}:${BUILD_TAG}"
    
    log_info "빌드 중: ${service}"
    
    # Dockerfile 경로에 따라 context 설정
    if [[ $dockerfile == "../"* ]]; then
        # 상위 디렉토리의 Dockerfile인 경우
        docker build -f "$dockerfile" -t "$image_name" ..
    else
        # 현재 디렉토리의 Dockerfile인 경우
        docker build -f "$dockerfile" -t "$image_name" .
    fi
    
    log_success "빌드 완료: ${service}"
}

# 이미지 푸시
push_image() {
    local service=$1
    local image_name="${REGISTRY_HOST}/${PROJECT_NAME}/${service}:${BUILD_TAG}"
    
    log_info "푸시 중: ${service}"
    docker push "$image_name"
    log_success "푸시 완료: ${service}"
}

# 메인 빌드 프로세스
main() {
    log_info "=== BrainBeaver 운영용 이미지 빌드 시작 ==="
    log_info "레지스트리: ${REGISTRY_HOST}"
    log_info "프로젝트: ${PROJECT_NAME}"
    log_info "태그: ${BUILD_TAG}"
    echo
    
    check_docker
    setup_local_registry
    
    log_info "이미지 빌드 시작..."
    
    # 모든 이미지 빌드
    for service in "${!IMAGES[@]}"; do
        dockerfile="${IMAGES[$service]}"
        build_image "$service" "$dockerfile"
    done
    
    log_info "이미지 푸시 시작..."
    
    # 모든 이미지 푸시
    for service in "${!IMAGES[@]}"; do
        push_image "$service"
    done
    
    echo
    log_success "=== 모든 이미지 빌드 및 푸시 완료 ==="
    
    # 빌드된 이미지 목록 출력
    log_info "빌드된 이미지 목록:"
    for service in "${!IMAGES[@]}"; do
        echo "  - ${REGISTRY_HOST}/${PROJECT_NAME}/${service}:${BUILD_TAG}"
    done
    
    echo
    log_info "운영 환경을 시작하려면 다음 명령을 실행하세요:"
    echo "  docker-compose -f docker-compose.prod.yml up -d"
}

# 도움말
show_help() {
    echo "BrainBeaver Production Build Script"
    echo ""
    echo "사용법:"
    echo "  $0 [OPTIONS]"
    echo ""
    echo "환경 변수:"
    echo "  REGISTRY_HOST    로컬 레지스트리 호스트 (기본값: localhost:5000)"
    echo "  BUILD_TAG        빌드 태그 (기본값: latest)"
    echo ""
    echo "예시:"
    echo "  $0                                    # 기본 설정으로 빌드"
    echo "  BUILD_TAG=v1.0.0 $0                  # 특정 태그로 빌드"
    echo "  REGISTRY_HOST=my-registry:5000 $0    # 커스텀 레지스트리 사용"
    echo ""
    echo "옵션:"
    echo "  -h, --help       이 도움말 표시"
}

# 인수 처리
case "${1:-}" in
    -h|--help)
        show_help
        exit 0
        ;;
    *)
        main "$@"
        ;;
esac