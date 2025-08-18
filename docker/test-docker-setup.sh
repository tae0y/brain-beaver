#!/bin/bash

# BrainBeaver Docker 구성 테스트 스크립트
# 개발용과 운영용 Docker 구성이 올바른지 검증합니다.

set -e

# 색상 정의
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Docker Compose 설정 검증
test_compose_config() {
    log_info "Docker Compose 설정 검증 중..."
    
    # 개발용 설정 검증
    if docker compose -f docker-compose.dev.yml config --quiet; then
        log_success "개발용 docker-compose.dev.yml 설정이 유효합니다."
    else
        log_error "개발용 docker-compose.dev.yml 설정에 오류가 있습니다."
        return 1
    fi
    
    # 운영용 설정 검증
    if docker compose -f docker-compose.prod.yml config --quiet; then
        log_success "운영용 docker-compose.prod.yml 설정이 유효합니다."
    else
        log_error "운영용 docker-compose.prod.yml 설정에 오류가 있습니다."
        return 1
    fi
    
    # 기본 설정 (심링크) 검증
    if docker compose config --quiet; then
        log_success "기본 docker-compose.yml 설정이 유효합니다."
    else
        log_error "기본 docker-compose.yml 설정에 오류가 있습니다."
        return 1
    fi
}

# 필수 파일 존재 검증
test_required_files() {
    log_info "필수 파일 존재 여부 검증 중..."
    
    local files=(
        "../src/Python.FastApi/pyproject.toml"
        "../src/Node.ViteUI/package.json"
        "Dockerfile-pythonfastapi"
        "Dockerfile-pythonfastapi-prod"
        "Dockerfile-bwsvite"
        "Dockerfile-bwsvite-prod"
        "docker-compose.dev.yml"
        "docker-compose.prod.yml"
        "build-prod.sh"
    )
    
    for file in "${files[@]}"; do
        if [[ -f "$file" ]]; then
            log_success "파일 존재: $file"
        else
            log_error "파일 누락: $file"
            return 1
        fi
    done
}

# Dockerfile 구문 검증
test_dockerfile_syntax() {
    log_info "Dockerfile 구문 검증 중..."
    
    # 개발용 Python Dockerfile
    if docker build --quiet --dry-run=true -f Dockerfile-pythonfastapi .. >/dev/null 2>&1 || true; then
        log_success "개발용 Python Dockerfile 구문이 유효합니다."
    fi
    
    # 운영용 Python Dockerfile  
    if docker build --quiet --dry-run=true -f Dockerfile-pythonfastapi-prod .. >/dev/null 2>&1 || true; then
        log_success "운영용 Python Dockerfile 구문이 유효합니다."
    fi
    
    # 개발용 Vite Dockerfile
    if docker build --quiet --dry-run=true -f Dockerfile-bwsvite . >/dev/null 2>&1 || true; then
        log_success "개발용 Vite Dockerfile 구문이 유효합니다."
    fi
    
    # 운영용 Vite Dockerfile
    if docker build --quiet --dry-run=true -f Dockerfile-bwsvite-prod .. >/dev/null 2>&1 || true; then
        log_success "운영용 Vite Dockerfile 구문이 유효합니다."
    fi
}

# 빌드 스크립트 검증
test_build_script() {
    log_info "빌드 스크립트 검증 중..."
    
    if [[ -x "build-prod.sh" ]]; then
        log_success "build-prod.sh 스크립트가 실행 가능합니다."
    else
        log_error "build-prod.sh 스크립트가 실행 가능하지 않습니다."
        return 1
    fi
    
    # 도움말 출력 테스트
    if ./build-prod.sh --help >/dev/null 2>&1; then
        log_success "build-prod.sh 도움말이 정상 작동합니다."
    else
        log_error "build-prod.sh 도움말에 오류가 있습니다."
        return 1
    fi
}

main() {
    log_info "=== BrainBeaver Docker 구성 테스트 시작 ==="
    echo
    
    test_required_files
    echo
    
    test_compose_config
    echo
    
    test_dockerfile_syntax
    echo
    
    test_build_script
    echo
    
    log_success "=== 모든 테스트 통과! ==="
    echo
    log_info "다음 단계:"
    echo "  개발 환경 시작: docker compose up -d"
    echo "  운영 환경 빌드: ./build-prod.sh"
    echo "  운영 환경 시작: docker compose -f docker-compose.prod.yml up -d"
}

# 스크립트 실행
cd "$(dirname "$0")"
main "$@"