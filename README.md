# Brain Beaver :beaver:

## 데모, 프로젝트 소개

<a href="https://brainbeaver.streamlit.app/" target="_blank">:bulb: Streamlit | DEMO</a> 

![](demo.png)
  
- 마크다운 파일을 지식단위로 분해하고 연관관계를 그래프화
- 연관관계에서 **시작점이 되는 경우가 많으면 연두색, 도착지는 초록색**
  - pgvector 코사인 유사도로 topk를 구한 다음
  - 벡터내적이 0.7 이상인 경우에만 연관있는 것으로 판단
- 웹검색시 **귀무가설이 참이라면 빨간 노드로 추가연결**
  - 귀무가설은 웹검색결과별 페르소나와 주장하는 내용을 추출
  - 전문가들 찬/반 의견을 다수결로 채택/기각
  - 채택하면 빨간 노드를 추가 연결해줌
  

## 더미 데이터를 사용한 데모 구동방법

가상환경과 의존성을 설치하고
```shell
python -m venv .venv
. .venvb/bin/activate
pip install -r requirements.txt
```

python/demo 페이지로 들어가서 바로 구동합니다!
```shell
streamlit run demo.py
```

    
## docker/자기 데이터를 사용해 구동하는 방법
  
M1 맥북에어 기준으로 로컬에서 구동하는 방법을 설명드립니다.
  

가상환경과 의존성을 설치하고
```shell
python -m venv .venv
. .venvb/bin/activate
pip install -r requirements.txt
```

docker 폴더로 진입해서 db와 dbadmin을 구동합니다.  
docker이미지가 없다면 빌드부터 해줍니다.
```shell
docker-compose build #관리자권한으로 실행
docker compose up
```
  
필요한 의존성을 설치하고 app.py에서 아래와 같이 루트경로, 샘플링, 테스트 개수를 조정합니다.
```python
# 마크다운 파일이 위치한 루트경로를 입력합니다.
root_dir = '/Users/bachtaeyeong/20_DocHub/TIL'

# 파일을 버킷 사이즈만큼 랜덤하게 샘플링합니다
file_list = sample_file_list(file_list=file_list, bucket_size=10)

# 파일을 정해진 테스트건수만큼만 처리합니다.
keyconcept_list = split_file_into_keyconcept(file_list=file_list[:10])
```
  
python 폴더로 이동해서 app.py 파일을 실행합니다.  
표준출력은 로그파일에 저장하고, tqdm 프로그레스바만 표시합니다.  
wandb를 적용해둬서 app.py만 실행해도 되긴합니다.  
```shell
python app.py > logs/$(date +%Y-%m-%d_%H:%M:%S).log
```
  
동일하게 python 폴더에서 streamlit을 실행합니다.
```shell
streamlit run view.py
```
  
로컬에서 구동한 데모를 삭제할때는 이렇게 합니다.
```shell
docker compose down #생성한 도커 컨테이너가 삭제됨
docker volume prune #도커 컨테이너에 할당되지 않은 가상 볼륨을 모두 삭제
```