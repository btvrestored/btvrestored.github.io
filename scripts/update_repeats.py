#!/usr/bin/env python3
"""Обновляет repeats.json списком завершённых эфиров из видео группы VK.

Запускается GitHub Action по расписанию (.github/workflows/update-repeats.yml) или кнопкой в окне scripts/gui.py.
Нужен секрет VK_TOKEN (сервисный ключ VK-приложения или токен группы).
Идущие и ожидающие трансляции пропускаются — запись появляется после конца эфира.
"""
import json, os, sys, urllib.parse, urllib.request

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))


def _embed(it):
    p = it.get("player") or ""
    if "video_ext.php" not in p:
        return None
    p = p.replace("https://vk.com/", "https://vkvideo.ru/").replace("http://vk.com/", "https://vkvideo.ru/")
    if "hd=" not in p:
        p += ("&" if "?" in p else "?") + "hd=4"
    return p


def update_repeats(token, root=ROOT, owner_id=-232964863, limit=24):
    """Возвращает (число записей, изменился ли файл). Ошибки — RuntimeError."""
    if not token:
        raise RuntimeError("VK_TOKEN is not set")
    out = os.path.join(root, "repeats.json")
    q = urllib.parse.urlencode({"owner_id": owner_id, "count": 100, "extended": 0,
                                "v": "5.199", "access_token": token})
    with urllib.request.urlopen("https://api.vk.com/method/video.get?" + q, timeout=30) as r:
        data = json.load(r)
    if "error" in data:
        raise RuntimeError("VK API error: %s" % data["error"].get("error_msg"))

    fresh = []
    for it in data["response"]["items"]:
        if it.get("live") or it.get("live_status") in ("waiting", "started", "upcoming"):
            continue                      # эфир ещё идёт
        if it.get("processing"):
            continue                      # видео ещё обрабатывается
        url = _embed(it)
        if not url:
            continue
        fresh.append({"oid": it["owner_id"], "id": it["id"], "title": it.get("title") or "",
                      "date": it.get("date"), "embed": url})

    try:
        old = json.load(open(out, encoding="utf-8")).get("items", [])
    except Exception:
        old = []

    seen = {(x["oid"], x["id"]) for x in fresh}
    items = fresh + [x for x in old if (x["oid"], x["id"]) not in seen]
    items.sort(key=lambda x: x.get("date") or 0, reverse=True)   # без даты — в конец
    items = items[:limit]

    new = json.dumps({"items": items}, ensure_ascii=False, indent=1) + "\n"
    try:
        same = open(out, encoding="utf-8").read() == new
    except FileNotFoundError:
        same = False
    if not same:
        open(out, "w", encoding="utf-8").write(new)
    return len(items), not same


def main():
    token = os.environ.get("VK_TOKEN")
    try:
        n, changed = update_repeats(token, ROOT, int(os.environ.get("VK_OWNER_ID", "-232964863")),
                                    int(os.environ.get("REPEATS_LIMIT", "24")))
    except RuntimeError as e:
        sys.exit(str(e))
    print("repeats.json updated: %d items" % n if changed else "no changes")


if __name__ == "__main__":
    main()
