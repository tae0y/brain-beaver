from concurrent.futures import ThreadPoolExecutor

class ThreadPool:
    """
    ThreadPoolExecutor를 사용하기 위한 Wrapper 클래스
    """
    def __init__(self, max_workers:int):
        self._thread_pool = ThreadPoolExecutor(max_workers=max_workers)

    def submit(self, fn, *args, **kwargs):
        return self._thread_pool.submit(fn, *args, **kwargs)

    def shutdown(self, wait_option:bool, cancel_futures_option:bool):
        self._thread_pool.shutdown(wait=wait_option, cancel_futures=cancel_futures_option)

    def __del__(self):
        self._thread_pool.shutdown(wait=True, cancel_futures=True)
        print('ThreadPool deleted!')