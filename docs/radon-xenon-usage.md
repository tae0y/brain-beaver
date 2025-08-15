# radon & xenon 사용법

## 의존성 설치

```bash
REPOSITORY_ROOT=$(git rev-parse --show-toplevel)
cd $REPOSITORY_ROOT/src/Python.FastApi
uv venv .venv #이미 가상환경이 있다면 생략
source .venv/bin/activate
uv sync --extra dev
```

## radon
- 코드 복잡도를 분석해서 평문으로 출력한다.
- 다음과 같은 옵션이 있다.
  - `radon cc`: Cyclomatic Complexity 함수/메서드/클래스의 복잡도를 등급으로 분석. 
    - 코드 분기(조건/반복) 수가 많을 수록 복잡도가 높음. 
    - 복잡도 높은 함수/클래스를 식별하여 리팩토링. 
  - `radon raw`: Raw Metrics 코드라인 대비 주석 비율을 집계해볼 수 있다.
    - `(C % L)`: 전체 라인(LOC) 대비 한 줄 주석(Single comments)의 비율
      - 예) (Single comments / LOC) × 100
    - `(C % S)`: 소스 코드 라인(SLOC) 대비 한 줄 주석의 비율
      - 예) (Single comments / SLOC) × 100
    - `(C + M % L)`: 전체 라인(LOC) 대비 한 줄 주석 + 여러 줄 주석(Multi)의 비율
      - 예) ((Single comments + Multi) / LOC) × 100
  - `radon mi`: Maintainability Index 가독성, 복잡도, 크기 등을 점수와 등급으로 분석.
  - `radon hal`: Halstead Metrics 복잡도 지표(연산자/피연산자 수, 난이도 등).
    - 코드의 계산적 복잡도와 개발/이해/테스트에 필요한 노력을 추정함.
    - 코드 난이도, 개발 비용, 테스트 비용을 예측.
    - volume, difficulty, effort, bugs 값이 높을수록 코드 품질 개선이 필요
      - `h1`: 고유 연산자(operator) 종류 수
      - `h2`: 고유 피연산자(operand) 종류 수
      - `N1`: 연산자 등장 횟수
      - `N2`: 피연산자 등장 횟수
      - `vocabulary`: h1 + h2, 전체 고유 토큰 종류 수
      - `length`: N1 + N2, 전체 토큰 등장 횟수
      - `calculated_length`: 이론적 코드 길이(공식 기반)
      - `volume`: 코드의 정보량(이해해야 할 정보의 양)
      - `difficulty`: 코드의 난이도(높을수록 이해/수정이 어려움)
      - `effort`: 코드 이해/수정에 필요한 노력(높을수록 어렵고 비용이 큼)
      - `time`: 코드 이해/수정에 필요한 시간(초 단위)
      - `bugs`: 잠재적 버그 수(이론적 추정치)
- 복잡도 등급은 다음과 같이 나뉜다.
  - `A`: 1~5 (매우 단순)
  - `B`: 6~10 (단순)
  - `C`: 11~20 (보통)
  - `D`: 21~30 (복잡)
  - `E`: 31~40 (매우 복잡)
  - `F`: 41 이상 (극도로 복잡)

- 다음과 같이 실행할 수 있다.

```bash
cd $REPOSITORY_ROOT
uv run radon cc src/Python.FastApi/ -a --min C --e ".venv,__pycache__,.pytest_cache" --show-closures
uv run radon raw src/Python.FastApi/ -s --e ".venv,__pycache__,.pytest_cache"
uv run radon mi src/Python.FastApi/ -s --min C -i "__pycache__"
uv run radon hal src/Python.FastApi/ -e ".venv,__pycache__,.pytest_cache"
```

- 출력결과는 다음과 같다.

```
# 샘플
path/to/the/source/file.py
    category linenum:colnum name - rating
    category linenum:colnum name - rating

# 실제 샘플
src/Python.FastApi/references/referencesservice.py
    M 73:4 ReferencesService.expand_one_concept_with_websearch - C
src/Python.FastApi/extract/extractservice.py
    M 154:4 ExtractService.extract_keyconcepts_from_data - C
    M 28:4 ExtractService.check_budget - C

3 blocks (classes, functions, methods) analyzed.
Average complexity: C (14.333333333333334)
```



## xenon
- 코드 복잡도를 분석하고, 기준치를 넘어서면 표준오류로 출력하고 exit code를 1로 반환한다.
- 내부적으로 radon을 호출하여 복잡도 등급을 검증한다.
- CI/CD에 사용하기 좋다.

```bash
cd $REPOSITORY_ROOT
uv run xenon \
 --max-absolute B \
 --max-modules B \
 --max-average A \
 src/Python.FastApi/ \
 -e ".venv,.pytest_cache,__pycache__" \
 --paths-in-front
```
