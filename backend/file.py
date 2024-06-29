import os

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