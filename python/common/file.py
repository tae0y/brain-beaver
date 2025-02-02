import os
import chardet
import traceback

def get_file_list_recursively(root_dir, ignore_dir_list) -> list[str]:
    """
    루트 디렉토리내 모든 파일의 목록을 재귀적으로 추출한다.
    """
    dir_list = []
    dir_list.append(root_dir)

    file_list = []

    while len(dir_list) > 0:
        cur_dir = dir_list.pop(0)
        #print(cur_dir)
        for entry in os.listdir(cur_dir):
            if entry not in ignore_dir_list:
                entry_path = os.path.join(cur_dir, entry)
                #print(f"{os.path.isdir(entry_path)} - {entry_path}")
                if os.path.isdir(entry_path):
                    dir_list.append(entry_path)
                else:
                    file_list.append(entry_path)

    #for file in file_list:
    #    print(file)
    #print(len(file_list))

    return file_list

def get_plaintext_from_filepath(filepath: str) -> str:
    """
    파일경로를 입력받아 인코딩에 관계없이 텍스트를 반환한다.
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
        text = ''

        if encoding is not None:
            try:
                text = raw_data.decode(encoding)
            except UnicodeDecodeError:
                pass
        
        if not text:
            for encoding in encodings_to_try:
                try:
                    text = raw_data.decode(encoding)
                    break
                except UnicodeDecodeError:
                    pass
        
        #print(f"(len:{len(text)}) / {encoding}  / {filepath}")
        
    return text