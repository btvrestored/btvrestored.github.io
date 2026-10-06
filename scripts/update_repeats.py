#!/usr/bin/env python3
"""Обновляет repeats.json списком завершённых эфиров из видео группы VK.

Запускается GitHub Action по расписанию (.github/workflows/update-repeats.yml).
Нужен секрет VK_TOKEN (сервисный ключ VK-приложения или токен группы).
Идущие и ожидающие трансляции пропускаются — запись появляется после конца эфира.
"""
import json, os, sys, time, urllib.parse, urllib.request

OWNER_ID = int(os.environ.get("VK_OWNER_ID", "-232964863"))   # id группы со знаком минус
LIMIT = int(os.environ.get("REPEATS_LIMIT", "24"))
OUT = os.path.join(os.path.dirname(__file__), "..", "repeats.json")
TOKEN = os.environ.get("VK_TOKEN")
if not TOKEN:
    sys.exit("VK_TOKEN is not set")

q = urllib.parse.urlencode({"owner_id": OWNER_ID, "count": 100, "extended": 0,
                            "v": "5.199", "access_token": TOKEN})
with urllib.request.urlopen("https://api.vk.com/method/video.get?" + q, timeout=30) as r:
    data = json.load(r)
if "error" in data:
    sys.exit("VK API error: %s" % data["error"].get("error_msg"))

def embed(it):
    p = it.get("player") or ""
    if "video_ext.php" not in p:
        return None
    p = p.replace("https://vk.com/", "https://vkvideo.ru/").replace("http://vk.com/", "https://vkvideo.ru/")
    if "hd=" not in p:
        p += ("&" if "?" in p else "?") + "hd=4"
    return p

fresh = []
for it in data["response"]["items"]:
    if it.get("live") or it.get("live_status") in ("waiting", "started", "upcoming"):
        continue                      # эфир ещё идёт
    if it.get("processing"):
        continue                      # видео ещё обрабатывается
    url = embed(it)
    if not url:
        continue
    fresh.append({"oid": it["owner_id"], "id": it["id"], "title": it.get("title") or "",
                  "date": it.get("date"), "embed": url})

try:
    old = json.load(open(OUT, encoding="utf-8")).get("items", [])
except Exception:
    old = []

seen = {(x["oid"], x["id"]) for x in fresh}
items = fresh + [x for x in old if (x["oid"], x["id"]) not in seen]
items.sort(key=lambda x: x.get("date") or 0, reverse=True)   # без даты — в конец
items = items[:LIMIT]

new = json.dumps({"items": items}, ensure_ascii=False, indent=1) + "\n"
try:
    same = open(OUT, encoding="utf-8").read() == new
except FileNotFoundError:
    same = False
if not same:
    open(OUT, "w", encoding="utf-8").write(new)
    print("repeats.json updated:", len(items), "items")
else:
    print("no changes")
