from concurrent.futures import ThreadPoolExecutor
from .constants import Constants

# 전역 스레드풀 초기화
# 예를 들어, 최대 스레드 개수를 7로 설정
constants = Constants.get_instance()
global_thread_pool = ThreadPoolExecutor(max_workers=constants.ollama_global_thread_pool)

def get_global_thread_pool() -> ThreadPoolExecutor:
    return global_thread_pool

def shutdown_global_thread_pool(wait_option:bool, cancel_futures_option:bool) -> None:
    print('shutdown_global_thread_pool called!')
    global_thread_pool.shutdown(wait=wait_option, cancel_futures=cancel_futures_option)
    print('shutdown_global_thread_pool completed!')