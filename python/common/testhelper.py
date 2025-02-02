import random

def sample_file_list(file_list: list) -> list:
    """
    파일목록을 랜덤하게 섞는다.
    """
    random.shuffle(file_list)
    #sample_size = len(file_list)//bucket_size
    #return file_list[:sample_size]
    return file_list
