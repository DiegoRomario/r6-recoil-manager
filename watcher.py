import json
import time
import re
import requests
import os
import subprocess
import psutil

# === Settings ===
LUA_SCRIPT_PATH = r""
GHUB_TRAY_PATH = r"C:\Program Files\LGHUB\system_tray\lghub_system_tray.exe"
SELECTED_OPERATOR_JSON_URL = "https://api.jsonbin.io/v3/b/683b58328561e97a501dfa6b/latest"
OPERATORS_JSON_URL = "https://gist.githubusercontent.com/DiegoRomario/72a427e60a63c513d6307546707be363/raw/86d2c79e56ce95c2c62a10621c7e854ba226bf76/operators.json"

HEADERS = {
    "X-Master-Key": "$2a$10$aDjTx/WeqrYEzvk5dl.rlevDhjGI.yauOyxHmVTkVZEkylLsZmjY.",
    "X-Bin-Meta": "false"
}

# === Load Operators from Gist ===
def load_operators_from_gist():
    try:
        response = requests.get(OPERATORS_JSON_URL)
        if response.status_code == 200:
            return response.json()
        else:
            print(f"[✗] Failed to load operators from Gist. Status: {response.status_code}")
            return {}
    except Exception as e:
        print(f"[✗] Error fetching operators JSON: {e}")
        return {}

# === Helper Functions ===
def fetch_selected_operator():
    try:
        response = requests.get(SELECTED_OPERATOR_JSON_URL, headers=HEADERS)
        if response.status_code == 200:
            return response.json()
        else:
            print(f"[✗] Failed to fetch selected operator. Status: {response.status_code}")
            return None
    except Exception as e:
        print(f"[✗] Error fetching JSON: {e}")
        return None

def find_operator(operators, role, name):
    try:
        if name == "[none]":
            return {"X": 0, "Y": 0}
        role_dict = operators.get(role, {})
        return role_dict.get(name, None)
    except Exception as e:
        print(f"[✗] Error while finding operator: {e}")
        return None

def update_lua_script(x, y):
    try:
        with open(LUA_SCRIPT_PATH, "r", encoding="utf-8") as f:
            content = f.read()

        content = re.sub(r"HorizontalRecoilCompensation\s*=\s*-?\d+", f"HorizontalRecoilCompensation = {x}", content)
        content = re.sub(r"VerticalRecoilCompensation\s*=\s*-?\d+", f"VerticalRecoilCompensation = {y}", content)

        with open(LUA_SCRIPT_PATH, "w", encoding="utf-8") as f:
            f.write(content)

        print("[✓] Lua script updated successfully.")
    except Exception as e:
        print(f"[✗] Failed to update Lua script: {e}")

def restart_ghub():
    ghub_processes = ["lghub.exe", "lghub_agent.exe", "lghub_updater.exe", "lghub_system_tray.exe"]
    for proc in psutil.process_iter(['pid', 'name']):
        if proc.info['name'] and proc.info['name'].lower() in ghub_processes:
            try:
                print(f"[✖] Terminating {proc.info['name']}")
                proc.terminate()
                proc.wait(timeout=10)
            except Exception as e:
                print(f"[!] Error terminating {proc.info['name']}: {e}")

    try:
        print("[→] Launching G HUB to system tray...")
        subprocess.Popen([GHUB_TRAY_PATH, "--background"], shell=False)
        print("[✓] G HUB started in tray.")
    except Exception as e:
        print(f"[✗] Failed to launch G HUB: {e}")

def countdown(seconds):
    print("🕒 Next check in:")
    for i in range(seconds, 0, -1):
        indent = "-" * (seconds - i + 1)
        print(f"{indent} {i}")
        time.sleep(1)

# === Main Loop ===
def main():
    print("▶️  R6 Recoil Watcher Started")
    previous_selection = None
    operators = load_operators_from_gist()

    while True:
        countdown(10)
        print("📜 Reading selected operator...")

        selection = fetch_selected_operator()
        if not selection:
            continue

        if selection == previous_selection:
            print("◻️  No changes detected.")
            continue

        previous_selection = selection
        role = selection.get("role")
        name = selection.get("operator")

        if name == "[none]":
            print(f"[✓] New Selection: {name}")
            x, y = 0, 0
        else:
            print(f"[✓] New Selection: {name} ({role})")
            operator_data = find_operator(operators, role, name)
            if not operator_data:
                print(f"[!] Operator not found: {name} ({role})")
                continue
            x = operator_data["X"]
            y = operator_data["Y"]
            grip = operator_data.get("GRIP", "N/A")
            barrel = operator_data.get("BARREL", "N/A")
            sights = operator_data.get("SIGHTS", "N/A")
            print(f"[✓] Applying: X = {x}, Y = {y}, Grip = {grip}, Barrel = {barrel}, Sights = {sights}")

        update_lua_script(x, y)
        restart_ghub()

        print("✅ Configuration applied.") 
        print("🕵️  Watching for changes...")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n🛑 Watcher stopped by user.")
