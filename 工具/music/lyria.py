# Lyria 2 配乐（Vertex AI lyria-002）：一条提示词出一段约 30 秒 48kHz WAV；每次请求前记账，到上限就停
import base64, json, os, subprocess, sys, urllib.request
PROJECT, LOC = "project-2000f509-2230-4dd4-bfe", "us-central1"
PRICE, CAP = float(os.environ.get("PRICE", "0.06")), float(os.environ.get("CAP_USD", "3"))
def book():
    s = json.load(open("spent.json")) if os.path.exists("spent.json") else {"usd": 0, "requests": 0}
    if s["usd"] + PRICE > CAP + 1e-9: return None
    s["usd"] = round(s["usd"] + PRICE, 2); s["requests"] += 1; json.dump(s, open("spent.json", "w")); return s["usd"]
tok = subprocess.check_output(["gcloud", "auth", "print-access-token"]).decode().strip()
url = f"https://{LOC}-aiplatform.googleapis.com/v1/projects/{PROJECT}/locations/{LOC}/publishers/google/models/lyria-002:predict"
shots = json.load(open(os.environ.get("SHOTS", "music.json"))); only = set(sys.argv[1:])
os.makedirs("out", exist_ok=True)
for s in shots:
    if only and s["id"] not in only: continue
    path = f"out/{s['id']}.wav"
    if os.path.exists(path): print("exists", s["id"]); continue
    total = book()
    if total is None: print("CAP reached", CAP); break
    body = {"instances": [{"prompt": s["prompt"], "negative_prompt": s.get("neg", "vocals, singing, lyrics, speech, voice, choir, electric guitar, drum kit, synth bass, EDM")}], "parameters": {"sample_count": 1}}
    req = urllib.request.Request(url, data=json.dumps(body).encode(), headers={"Authorization": "Bearer " + tok, "Content-Type": "application/json"})
    try:
        r = json.load(urllib.request.urlopen(req, timeout=300))
    except Exception as e:
        print("ERR", s["id"], str(e)[:200], getattr(e, "read", lambda: b"")()[:300]); continue
    preds = r.get("predictions") or []
    if not preds: print("no audio", s["id"], str(r)[:300]); continue
    b64 = preds[0].get("bytesBase64Encoded") or preds[0].get("audioContent")
    open(path, "wb").write(base64.b64decode(b64)); print("ok", s["id"], os.path.getsize(path), "booked", total)
