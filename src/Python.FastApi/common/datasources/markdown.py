from typing import Tuple
import os
import random
import chardet
import traceback

class Markdown():
    """
    마크다운 문서가 저장된 루트 디렉토리를 입력받아 데이터소스를 처리
    """
    file_list = None
    data_list = None
    lazy_list = None

    def __init__(self, root_dir: str):
        """
        Markdown 클래스 생성자
        - param
            - root_dir: 마크다운 문서가 저장된 루트 디렉토리
        """
        if root_dir is None:
            raise ValueError("root_dir is None.")
        else:
            self.root_dir = root_dir
        self.file_list = None


    def load_file_list_recursively(self, ignore_dir_list):
        """
        루트 디렉토리내 모든 파일의 목록을 재귀적으로 추출한다.
        - param
          - ignore_dir_list: 무시할 디렉토리 목록
        - return 
          - list[str] 타입으로 파일 목록을 반환
        """
        if ignore_dir_list is None:
            ignore_dir_list = [
                '.DS_Store', '.git', '.gitignore', '.vscode', '.obsidian', 
                '.smart-env', 'Res', 'Chats', 'smart-chats', 'Excalidraw', 
                '.smtcmp_vector_db.tar.gz', '.smtcmp_chat_histories'
            ]

        self.file_list = []

        dir_list = []
        dir_list.append(self.root_dir)
        while len(dir_list) > 0:
            current = dir_list.pop(0)
            for next in os.listdir(current):
                if (next not in ignore_dir_list):
                    next_path = os.path.join(current, next)
                    if os.path.isdir(next_path):
                        dir_list.append(next_path)
                    elif next_path.endswith('.md'): #마크다운 파일만 목록에 추가
                        self.file_list.append(next_path)

        print(f"LOG-DEBUG: File list loaded - {len(self.file_list)} (load_file_list_recursively)")


    def get_data_list(self, shuffle_flag: bool, ignore_dir_list: list[str]):
        """
        데이터소스의 모든 데이터를 반환한다.
        """
        raise NotImplementedError("마크다운 데이터소스는 지원하지 않는 기능입니다.")


    def get_lazy_list(self, shuffle_flag: bool, ignore_dir_list: list[str]) -> list[Tuple[str, callable]]:
        """
        데이터소스의 데이터로더 이터레이터를 반환한다.

        - param
            - shuffle_flag: 데이터를 랜덤하게 섞을지 여부
            - ignore_dir_list: 무시할 디렉토리 목록

        - return
            - list[Tuple[str, callable]] 파일경로, 파일 데이터로더 함수 투플의 리스트
            - 파일 데이터로더는 loader() 형태로 호출하여 사용하면 된다
        """
        if self.lazy_list is None:
            if self.file_list is None:
                self.load_file_list_recursively(ignore_dir_list)

            file_list = self.file_list[:] # copy
            if shuffle_flag:
                random.shuffle(file_list)

            loader_list = []
            for filepath in file_list:
                loader_func = lambda f=filepath: self.get_plaintext_from_filepath(f)
                loader_list.append((filepath, loader_func))

            self.lazy_list = loader_list

        return self.lazy_list

    def get_plaintext_from_filepath(self, filepath: str) -> str:
        """
        파일경로를 입력받아 인코딩에 관계없이 텍스트를 반환한다.

        - param
            - filepath: 파일경로
        - return
            - str 타입으로 텍스트를 반환
        """
        encodings_to_try = [
            'utf-8',
            'utf-8-sig',
            'euc-kr',
            'cp949',
            'latin1',
            'iso-8859-1',
            'cp1252'
        ]

        with open(filepath, 'rb') as f:
            raw_data = f.read()
            encoding = chardet.detect(raw_data)['encoding']
            text = None

            if encoding is not None:
                try:
                    text = raw_data.decode(encoding)
                except UnicodeDecodeError:
                    pass

            if text is None:
                for encoding in encodings_to_try:
                    try:
                        text = raw_data.decode(encoding)
                        break
                    except UnicodeDecodeError:
                        pass

            if not text:
                if len(raw_data) > 0:
                    print(f"LOG-ERROR: Failed to decode the file - {filepath} (get_plaintext_from_filepath)")

        return text
