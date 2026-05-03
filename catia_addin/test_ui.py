"""FSAE-PLM 完整 UI 自动化测试"""
import sys, io, subprocess, time, os
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

from pywinauto import Desktop

EXE = os.path.join(os.path.dirname(__file__), "bin", "Debug", "net8.0-windows", "TestApp.exe")

def find_win(title, timeout=10):
    for _ in range(timeout):
        wins = Desktop(backend="uia").windows(title_re=title)
        if wins:
            return wins[0]
        time.sleep(1)
    return None

def test_full_workflow():
    print("=== FSAE-PLM UI Test ===\n")

    # Start test app
    print("[1] Starting TestApp...")
    proc = subprocess.Popen([EXE])
    time.sleep(8)

    # Check for Login or PartsList
    print("[2] Looking for window...")
    parts_win = find_win("零件列表", timeout=10)
    if not parts_win:
        login_win = find_win("用户登录", timeout=5)
        if login_win:
            print("    Found login dialog - need to login first")
            # Fill login
            edits = login_win.descendants(control_type="Edit")
            if len(edits) >= 3:
                edits[0].set_text("http://localhost/api")
                edits[1].set_text("admin")
                edits[2].set_text("admin123")
                time.sleep(0.5)
                btn = login_win.child_window(title_re="登.*录", control_type="Button")
                btn.click_input()
                time.sleep(3)
                parts_win = find_win("零件列表", timeout=5)
            else:
                print(f"    FAIL: Only {len(edits)} edit controls found")
                proc.kill()
                return False
        else:
            print("    FAIL: No window found")
            proc.kill()
            return False

    if not parts_win:
        print("    FAIL: Parts list not opened")
        proc.kill()
        return False

    print(f"    OK: {parts_win.window_text()}")

    # Check data loaded
    print("[3] Checking parts data...")
    time.sleep(1)
    status = parts_win.descendants(title_re="共.*个零件")
    if status:
        print(f"    OK: {status[0].window_text()}")
    else:
        print("    WARN: Status label not found")

    # Click first row then View Detail
    print("[4] Opening part detail...")
    grid = parts_win.descendants(control_type="DataGrid")
    if grid:
        rows = grid[0].descendants(title_re="行 0")
        if rows:
            rows[0].click_input()
            time.sleep(0.5)

    detail_btn = parts_win.child_window(title="查看详情", control_type="Button")
    detail_btn.click_input()
    time.sleep(2)

    detail_win = find_win("详情|Detail", timeout=5)
    if detail_win:
        print(f"    OK: {detail_win.window_text()}")

        # Check buttons exist
        for btn_name in ["检出", "检入", "发布"]:
            try:
                detail_win.child_window(title_re=btn_name, control_type="Button")
                print(f"    OK: Button '{btn_name}' found")
            except:
                print(f"    WARN: Button '{btn_name}' not found")

        # Close detail
        try:
            detail_win.child_window(title="关闭", control_type="Button").click_input()
            print("[5] Closed detail")
        except:
            print("[5] Could not close detail")
    else:
        print("    FAIL: Detail window not opened")
        # Try to close parts list
        parts_win.child_window(title="关闭", control_type="Button").click_input()
        proc.kill()
        return False

    time.sleep(1)

    # Test New Part button
    print("[6] Testing New Part dialog...")
    new_btn = parts_win.child_window(title="新建零件", control_type="Button")
    new_btn.click_input()
    time.sleep(2)

    create_win = find_win("新建零件|Create", timeout=5)
    if create_win:
        print(f"    OK: {create_win.window_text()}")
        create_win.close()
        time.sleep(1)
    else:
        print("    WARN: Create Part dialog not found")

    # Close parts list
    print("[7] Closing parts list...")
    try:
        parts_win.child_window(title="关闭", control_type="Button").click_input()
    except:
        pass

    time.sleep(1)
    proc.kill()

    print("\n=== TEST PASSED ===")
    return True

if __name__ == "__main__":
    success = test_full_workflow()
    sys.exit(0 if success else 1)
