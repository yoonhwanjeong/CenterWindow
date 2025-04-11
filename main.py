import tkinter as tk
from tkinter import ttk
import win_utils
import tkinter.messagebox as tkmb
import argparse
import sys

class ProcessCenterApp:
    def __init__(self, root=None):
        self.root = root
        if root:
            self.root.title("프로세스 창 중앙 이동")

            self.all_processes_with_windows = win_utils.get_all_processes_with_windows()

            # 프로세스 필터링 입력 필드
            self.filter_label = ttk.Label(root, text="프로세스 이름 필터:")
            self.filter_label.pack(pady=(10, 0), padx=10, anchor="w")
            self.filter_entry = ttk.Entry(root)
            self.filter_entry.pack(pady=5, padx=10, fill="x")
            self.filter_entry.bind("<KeyRelease>", self.update_process_list)

            # 새로고침 버튼
            self.refresh_button = ttk.Button(root, text="새로고침", command=self.refresh_process_list)
            self.refresh_button.pack(pady=5, padx=10, fill="x")

            # 프로세스 목록 상자
            self.process_listbox = tk.Listbox(root, selectmode=tk.SINGLE, width=60)
            self.process_listbox.pack(pady=10, padx=10, fill="both", expand=True)

            # 확인 버튼
            self.confirm_button = ttk.Button(root, text="선택 및 확인", command=self.on_confirm)
            self.confirm_button.pack(pady=5, padx=10, fill="x")

            self.update_process_list() # 초기 목록 표시

    def update_process_list(self, event=None):
        """텍스트 필드 입력에 따라 프로세스 목록을 필터링하여 업데이트합니다."""
        filter_text = self.filter_entry.get().lower()
        self.process_listbox.delete(0, tk.END)
        for pid, name in self.all_processes_with_windows:
            if filter_text in name.lower():
                self.process_listbox.insert(tk.END, f"{pid} - {name}")

    def refresh_process_list(self):
        """프로세스 목록을 다시 불러오고 화면을 업데이트합니다."""
        self.all_processes_with_windows = win_utils.get_all_processes_with_windows()
        self.update_process_list()

    def show_window_selection_dialog(self, windows_with_text):
        """창 선택 다이얼로그를 표시하고 선택된 hwnd를 반환합니다."""
        dialog = tk.Toplevel(self.root)
        dialog.title("창 선택")
        listbox = tk.Listbox(dialog, selectmode=tk.SINGLE, width=60)
        for hwnd, text in windows_with_text:
            listbox.insert(tk.END, f"HWND: {hex(hwnd)}, 텍스트: {text}")
        listbox.pack(pady=10, padx=10)

        chosen_hwnd = None

        def on_select():
            nonlocal chosen_hwnd
            selected_index = listbox.curselection()
            if selected_index:
                selected_item = listbox.get(selected_index[0])
                hwnd_str = selected_item.split(",")[0].split(":")[1].strip()
                try:
                    chosen_hwnd = int(hwnd_str, 16)  # 16진수 문자열을 정수로 변환
                    dialog.destroy()
                except ValueError:
                    tkmb.showerror("오류", "잘못된 창 핸들 형식입니다.")
            else:
                tkmb.showinfo("알림", "창을 선택해주세요.")

        confirm_button = ttk.Button(dialog, text="선택", command=on_select)
        confirm_button.pack(pady=5, padx=10)

        dialog.wait_window()  # 다이얼로그가 닫힐 때까지 기다림
        return chosen_hwnd

    def on_confirm(self):
        """확인 버튼 클릭 시 선택된 프로세스의 창을 중앙으로 이동시킵니다."""
        selected_index = self.process_listbox.curselection()
        if selected_index:
            selected_process_str = self.process_listbox.get(selected_index[0])
            pid_str = selected_process_str.split(" - ")[0]
            try:
                pid = int(pid_str)
                windows = win_utils.get_process_windows(pid)
                if windows:
                    if len(windows) > 1:
                        windows_with_text = win_utils.get_window_texts_from_hwnd_list(windows)
                        selected_hwnd = self.show_window_selection_dialog(windows_with_text)
                        if selected_hwnd:
                            win_utils.center_window(selected_hwnd)
                    elif len(windows) == 1:
                        win_utils.center_window(windows[0])
                    else:
                        tkmb.showerror("오류", f"{selected_process_str.split(' - ')[1]} 프로세스의 창을 찾을 수 없습니다.")
                else:
                    tkmb.showerror("오류", f"{selected_process_str.split(' - ')[1]} 프로세스의 창을 찾을 수 없습니다.")
            except ValueError:
                tkmb.showerror("오류", "잘못된 프로세스 ID입니다.")
        else:
            tkmb.showinfo("알림", "프로세스를 선택해주세요.")

def run_headless(pid):
    """GUI 없이 특정 PID의 창을 선택하여 중앙으로 이동합니다."""
    try:
        pid_int = int(pid)
        windows = win_utils.get_process_windows(pid_int)
        if windows:
            if len(windows) > 1:
                windows_with_text = win_utils.get_window_texts_from_hwnd_list(windows)
                print(f"PID {pid}에 대해 여러 개의 창이 발견되었습니다. 번호를 선택하세요:")
                for i, (hwnd, text) in enumerate(windows_with_text):
                    print(f"{i+1}. HWND: {hex(hwnd)}, 텍스트: {text}")

                while True:
                    try:
                        choice = int(input("선택할 창 번호: "))
                        if 1 <= choice <= len(windows_with_text):
                            selected_hwnd = windows_with_text[choice - 1][0]
                            win_utils.center_window(selected_hwnd)
                            print(f"선택된 창 (HWND: {hex(selected_hwnd)})을 중앙으로 이동했습니다.")
                            break
                        else:
                            print("잘못된 번호입니다. 다시 입력해주세요.")
                    except ValueError:
                        print("숫자를 입력해주세요.")
            elif len(windows) == 1:
                win_utils.center_window(windows[0])
                print(f"PID {pid}의 창 (HWND: {hex(windows[0])})을 중앙으로 이동했습니다.")
            else:
                print(f"PID {pid}에 해당하는 창을 찾을 수 없습니다.")
        else:
            print(f"PID {pid}에 해당하는 창을 찾을 수 없습니다.")
    except ValueError:
        print("오류: PID는 정수여야 합니다.")
    except Exception as e:
        print(f"오류 발생: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="프로세스 창 중앙 이동 유틸리티")
    parser.add_argument("--headless", action="store_true", help="GUI 없이 실행")
    parser.add_argument("-p", "--pid", type=str, help="중앙으로 이동할 프로세스의 PID")

    args = parser.parse_args()

    if args.headless:
        if args.pid:
            run_headless(args.pid)
        else:
            print("오류: --headless 모드에서는 -p 또는 --pid 인자를 함께 제공해야 합니다.")
            sys.exit(1)
    else:
        root = tk.Tk()
        app = ProcessCenterApp(root)
        root.mainloop()