import psutil
import win32gui as wg
import win32con as wc
import win32api as wa
import win32process as wp

def is_system_process(pid):
    """주어진 PID가 시스템 프로세스인지 확인합니다."""
    try:
        process = psutil.Process(pid)
        if process.username().lower() in ["nt authority\\system", "system"]:
            return True
        return False
    except psutil.NoSuchProcess:
        return False
    except Exception as e:
        print(f"프로세스 정보 확인 오류 (PID: {pid}): {e}")
        return False

def get_process_windows(pid):
    """특정 PID의 모든 보이는 최상위 창 핸들을 리스트로 반환합니다."""
    windows = []
    def callback(hwnd, extra):
        if wg.IsWindowVisible(hwnd) and wp.GetWindowThreadProcessId(hwnd)[1] == pid:
            windows.append(hwnd)
        return True
    wg.EnumWindows(callback, None)
    return windows

def has_visible_window(pid):
    """특정 PID에 보이는 최상위 창이 하나 이상 있는지 확인합니다."""
    return len(get_process_windows(pid)) > 0

def get_all_processes_with_windows():
    """실행 중이며 창을 가진 프로세스 목록을 (pid, 이름) 튜플의 리스트로 반환합니다."""
    processes = []
    for proc in psutil.process_iter(['pid', 'name']):
        pid = proc.info['pid']
        if not is_system_process(pid) and has_visible_window(pid):
            processes.append((pid, proc.info['name']))
    return processes

def get_window_texts_from_hwnd_list(hwnd_list):
    """hwnd 목록을 받아서 (hwnd, 창 텍스트) 튜플의 리스트를 반환합니다."""
    window_texts = []
    for hwnd in hwnd_list:
        try:
            text = wg.GetWindowText(hwnd)
            window_texts.append((hwnd, text))
        except Exception as e:
            print(f"창 텍스트 가져오기 오류 (HWND: {hwnd}): {e}")
            window_texts.append((hwnd, ""))  # 오류 발생 시 빈 텍스트로 처리
    return window_texts

def center_window(hwnd):
    """주어진 창 핸들을 모니터 중앙으로 이동시킵니다."""
    try:
        monitor_info = wa.GetMonitorInfo(wa.MonitorFromWindow(hwnd))
        monitor_rect = monitor_info['Monitor']
        monitor_width = monitor_rect[2] - monitor_rect[0]
        monitor_height = monitor_rect[3] - monitor_rect[1]

        window_rect = wg.GetWindowRect(hwnd)
        window_width = window_rect[2] - window_rect[0]
        window_height = window_rect[3] - window_rect[1]

        x = monitor_rect[0] + (monitor_width - window_width) // 2
        y = monitor_rect[1] + (monitor_height - window_height) // 2

        wg.SetWindowPos(hwnd, wc.HWND_TOP, x, y, 0, 0, wc.SWP_NOSIZE)
    except Exception as e:
        print(f"창 중앙 이동 오류: {e}")