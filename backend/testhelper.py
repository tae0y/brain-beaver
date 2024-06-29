import random

def sample_file_list(file_list: list, bucket_size: int) -> list:
    """
    파일목록을 버킷사이즈만큼 랜덤하게 샘플링한다
    """
    random.shuffle(file_list)
    return file_list[:bucket_size]
    