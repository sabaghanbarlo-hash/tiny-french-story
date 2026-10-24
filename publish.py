#!/usr/bin/env python3
"""Publish a rendered Tiny French video to Instagram as a Reel via Composio.

Usage: publish.py CAPTION_FILE VIDEO_BASENAME [--check]
  --check  only verify the key + Instagram connection, post nothing.
Env: COMPOSIO_API_KEY (secret), PAGES_BASE (public site URL), IG_ACCOUNT (Composio account label, default "Tiny French").
Exits non-zero unless Instagram returned a published media id, so the workflow never claims a post that did not happen.
"""
import json, os, sys, time, urllib.request, urllib.error

args = [a for a in sys.argv[1:] if not a.startswith("--")]
CHECK = "--check" in sys.argv
KEY = os.environ.get("COMPOSIO_API_KEY", "").strip()
if not KEY:
    sys.exit("COMPOSIO_API_KEY is not set. Add it as a repository secret.")
MCP_URL = "https://connect.composio.dev/mcp"
_s = {"id": None, "n": 0}


def _post(payload):
    h = {"x-consumer-api-key": KEY, "Content-Type": "application/json", "Accept": "application/json, text/event-stream"}
    if _s["id"]:
        h["Mcp-Session-Id"] = _s["id"]
    req = urllib.request.Request(MCP_URL, data=json.dumps(payload).encode(), headers=h, method="POST")
    try:
        r = urllib.request.urlopen(req, timeout=400)
    except urllib.error.HTTPError as e:
        sys.exit(f"Composio said HTTP {e.code}: {e.read().decode()[:400]}")
    if r.headers.get("Mcp-Session-Id"):
        _s["id"] = r.headers.get("Mcp-Session-Id")
    raw = r.read().decode()
    if not raw.strip():
        return None
    if "data:" in raw and not raw.lstrip().startswith("{"):
        for m in reversed([l[5:].strip() for l in raw.splitlines() if l.startswith("data:")]):
            try:
                return json.loads(m)
            except ValueError:
                continue
        return None
    return json.loads(raw)


def _rpc(method, params=None, notify=False):
    msg = {"jsonrpc": "2.0", "method": method}
    if params is not None:
        msg["params"] = params
    if not notify:
        _s["n"] += 1
        msg["id"] = _s["n"]
    return _post(msg)


def call(slug, arguments):
    r = _rpc("tools/call", {"name": "COMPOSIO_MULTI_EXECUTE_TOOL", "arguments": {"tools": [
        {"tool_slug": slug, "account": os.environ.get("IG_ACCOUNT") or "Tiny French", "arguments": arguments}],
        "sync_response_to_workbench": False}})
    if not r or "error" in r:
        sys.exit(f"{slug} failed: {str(r)[:500]}")
    res = r.get("result", {})
    text = "".join(c.get("text", "") for c in res.get("content", []) if isinstance(c, dict))
    try:
        top = json.loads(text)
    except ValueError:
        sys.exit(f"{slug}: unreadable answer from Composio: {text[:400]}")
    items = (top.get("data") or {}).get("results") or []
    if res.get("isError") or not top.get("successful", True) or not items:
        sys.exit(f"{slug} failed: {str((items[0] if items else {}).get('error') or top.get('error') or top)[:600]}")
    resp = items[0].get("response", {})
    if not resp.get("successful", True):
        sys.exit(f"{slug} failed: {str(resp.get('error') or resp)[:600]}")
    return resp


def find_id(o):
    if isinstance(o, dict):
        if isinstance(o.get("id"), (str, int)):
            return str(o["id"])
        for v in o.values():
            f = find_id(v)
            if f:
                return f
    return None


r = _rpc("initialize", {"protocolVersion": "2025-03-26", "capabilities": {}, "clientInfo": {"name": "tiny-french-story", "version": "1.0"}})
if not r or "error" in r:
    sys.exit(f"Composio initialize failed: {str(r)[:400]}")
_rpc("notifications/initialized", notify=True)

if CHECK:
    info = call("INSTAGRAM_GET_USER_INFO", {"ig_user_id": "me", "fields": "id,username,account_type"})
    print("CHECK OK. Instagram account:", json.dumps(info.get("data"), ensure_ascii=False))
    sys.exit(0)

caption_file, base = (args + ["", ""])[:2]
caption = open(caption_file, encoding="utf-8").read().strip()
site = os.environ.get("PAGES_BASE", "").rstrip("/")
url = f"{site}/videos/{base}.mp4"
print("Waiting for the video to be reachable:", url, flush=True)
for _ in range(60):
    try:
        if urllib.request.urlopen(urllib.request.Request(url, method="HEAD"), timeout=20).status == 200:
            break
    except Exception:
        pass
    time.sleep(10)
else:
    sys.exit("The video URL never became reachable (is GitHub Pages enabled with 'GitHub Actions' as its source?).")

payload = {"ig_user_id": "me", "video_url": url, "media_type": "REELS", "caption": caption, "share_to_feed": True}
cover = f"{site}/videos/{base}.jpg"
try:
    if urllib.request.urlopen(urllib.request.Request(cover, method="HEAD"), timeout=20).status == 200:
        payload["cover_url"] = cover
except Exception:
    print("No cover image online; Instagram will choose a frame.")
c = call("INSTAGRAM_POST_IG_USER_MEDIA", payload)
cid = find_id(c.get("data"))
if not cid:
    sys.exit("Instagram did not return a media container id; nothing was published.")
p = call("INSTAGRAM_POST_IG_USER_MEDIA_PUBLISH", {"ig_user_id": "me", "creation_id": cid, "max_wait_seconds": 300})
pid = find_id(p.get("data"))
if not pid:
    sys.exit("Instagram did not confirm the publish; check the account before retrying.")
print("PUBLISHED on Instagram, media id:", pid)
