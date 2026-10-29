#!/usr/bin/env python3
"""Обновляет repeats.json записями эфиров из VK Видео.

Запускается GitHub Action по расписанию (.github/workflows/update-repeats.yml) или кнопкой в окне scripts/gui.py.
Нужен секрет VK_TOKEN (сервисный ключ VK-приложения или токен группы).

Что делает:
  • читает ВСЕ видео владельца(ев) постранично (не только первые 100);
  • владельцев может быть несколько: VK_OWNER_IDS="-232964863,@btv_restored" — числа (группа с минусом) или адреса
    каналов/страниц VK Видео (@btv_restored, https://vkvideo.ru/@btv_restored) — они переводятся в ID через API;
  • кроме общего списка, просматриваются и все альбомы владельца;
  • идущие, ожидающие и ещё обрабатываемые трансляции пропускает — запись появится после конца эфира;
  • если VK не отдал готовый плеер, строит ссылку-встройку по owner_id и id;
  • в журнал пишет, сколько записей найдено и почему какие-то пропущены.
"""
import json, os, sys, urllib.parse, urllib.request

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
DEFAULT_OWNER = "-232964863,@btv_restored"
LIVE_NOW = ("waiting", "started", "upcoming")


def _embed(it):
    """Ссылка для iframe. Если VK не прислал player — собираем сами (работает для публичных видео)."""
    p = it.get("player") or ""
    if "video_ext.php" in p:
        p = p.replace("https://vk.com/", "https://vkvideo.ru/").replace("http://vk.com/", "https://vkvideo.ru/")
    else:
        p = "https://vkvideo.ru/video_ext.php?oid=%s&id=%s" % (it["owner_id"], it["id"])
        if it.get("access_key"):
            p += "&hash=" + str(it["access_key"])
    if "hd=" not in p:
        p += ("&" if "?" in p else "?") + "hd=4"
    return p


def _vk(method, token, **params):
    params.update({"v": "5.199", "access_token": token})
    with urllib.request.urlopen("https://api.vk.com/method/%s?%s" % (method, urllib.parse.urlencode(params)), timeout=30) as r:
        data = json.load(r)
    if "error" in data:
        raise RuntimeError("VK API %s: %s" % (method, data["error"].get("error_msg")))
    return data["response"]


def _owners(owner_id):
    """Список владельцев: числа или адреса (@имя, ссылка). Числа — как есть, адреса позже переводятся в ID."""
    if isinstance(owner_id, (list, tuple)):
        raw = owner_id
    else:
        raw = str(owner_id or DEFAULT_OWNER).replace(";", ",").split(",")
    out = []
    for x in raw:
        x = str(x).strip()
        if not x:
            continue
        try:
            out.append(int(x))
        except ValueError:
            out.append(x)
    return out or [DEFAULT_OWNER]


def _resolve(token, owner, log):
    """Числовой ID или адрес VK -> owner_id. Для сообщества возвращает отрицательный ID."""
    if isinstance(owner, int):
        return owner
    name = owner.rstrip("/").split("/")[-1].lstrip("@")
    errors = []

    # Some VK token/profile types cannot call utils.resolveScreenName. Try the
    # dedicated community/user lookups as fallbacks; both accept screen names.
    try:
        res = _vk("utils.resolveScreenName", token, screen_name=name)
        if res and res.get("object_id"):
            oid = -int(res["object_id"]) if res.get("type") in ("group", "public", "event") else int(res["object_id"])
            log("адрес %s → owner_id %s (%s)" % (owner, oid, res.get("type")))
            return oid
        errors.append("utils.resolveScreenName не нашёл адрес")
    except RuntimeError as e:
        errors.append(str(e))

    try:
        groups = _vk("groups.getById", token, group_id=name)
        if isinstance(groups, dict):
            groups = [groups]
        if groups:
            oid = -int(groups[0]["id"])
            log("адрес %s → owner_id %s (groups.getById)" % (owner, oid))
            return oid
    except (RuntimeError, KeyError, TypeError, ValueError) as e:
        errors.append(str(e))

    try:
        users = _vk("users.get", token, user_ids=name)
        if isinstance(users, dict):
            users = [users]
        if users:
            oid = int(users[0]["id"])
            log("адрес %s → owner_id %s (users.get)" % (owner, oid))
            return oid
    except (RuntimeError, KeyError, TypeError, ValueError) as e:
        errors.append(str(e))

    detail = "; ".join(errors[-3:])
    raise RuntimeError(
        "Не удалось определить VK-адрес «%s». Укажите числовой owner_id "
        "(для сообщества — с минусом). Детали: %s" % (owner, detail)
    )


def _list(token, owner, album_id=None):
    items, offset, total = [], 0, None
    while True:
        params = {"owner_id": owner, "count": 200, "offset": offset, "extended": 0}
        if album_id is not None:
            params["album_id"] = album_id
        resp = _vk("video.get", token, **params)
        page = resp.get("items", [])
        total = resp.get("count", total)
        items += page
        offset += len(page)
        if not page or (total is not None and offset >= total) or offset >= 2000:
            break
    return items


def _fetch_all(token, owner, log):
    """Все видео владельца: общий список + каждый альбом (дубли убираются)."""
    got = {}
    for it in _list(token, owner):
        got[(it["owner_id"], it["id"])] = it
    n_main = len(got)
    try:
        albums = _vk("video.getAlbums", token, owner_id=owner, count=100).get("items", [])
    except RuntimeError as e:
        albums = []
        log("альбомы недоступны: %s" % e)
    for al in albums:
        try:
            for it in _list(token, owner, al["id"]):
                got.setdefault((it["owner_id"], it["id"]), it)
        except RuntimeError as e:
            log("альбом «%s»: %s" % (al.get("title"), e))
    log("owner %s: общий список — %d видео, альбомов — %d, всего уникальных — %d" % (owner, n_main, len(albums), len(got)))
    return list(got.values())


def update_repeats(token, root=ROOT, owner_id=DEFAULT_OWNER, limit=24, log=print):
    """Возвращает (число записей, изменился ли файл). Ошибки — RuntimeError."""
    if not token:
        raise RuntimeError("VK_TOKEN is not set")
    out = os.path.join(root, "repeats.json")

    fresh, skipped = [], {}
    fresh_keys = set()
    owners = []
    for raw_owner in _owners(owner_id):
        try:
            resolved = _resolve(token, raw_owner, log)
        except RuntimeError as e:
            # One unsupported alias must not prevent all other known numeric
            # owners from refreshing the archive.
            log("владелец %s пропущен: %s" % (raw_owner, e))
            continue
        if resolved not in owners:
            owners.append(resolved)
    if not owners:
        raise RuntimeError("Не удалось определить ни одного владельца VK; repeats.json не изменён.")

    for owner in owners:
        for it in _fetch_all(token, owner, log):
            why = None
            if it.get("live") or it.get("live_status") in LIVE_NOW:
                why = "эфир ещё идёт или ожидается"
            elif it.get("processing"):
                why = "видео ещё обрабатывается"
            if why:
                skipped.setdefault(why, []).append(it.get("title") or str(it.get("id")))
                continue
            key = (it["owner_id"], it["id"])
            if key in fresh_keys:
                continue
            fresh_keys.add(key)
            fresh.append({"oid": it["owner_id"], "id": it["id"], "title": (it.get("title") or "").strip(),
                          "date": it.get("date"), "embed": _embed(it)})
    for why, names in skipped.items():
        log("пропущено (%s): %d — %s" % (why, len(names), "; ".join(names[:5])))

    try:
        with open(out, encoding="utf-8") as f:
            old = json.load(f).get("items", [])
    except Exception:
        old = []

    seen = {(x["oid"], x["id"]) for x in fresh}
    items = fresh + [x for x in old if (x["oid"], x["id"]) not in seen]
    items.sort(key=lambda x: x.get("date") or 0, reverse=True)   # без даты — в конец
    items = items[:limit]
    if items:
        log("самая свежая запись: %s" % (items[0].get("title") or items[0]["id"]))

    new = json.dumps({"items": items}, ensure_ascii=False, indent=1) + "\n"
    try:
        with open(out, encoding="utf-8") as f:
            same = f.read() == new
    except FileNotFoundError:
        same = False
    if not same:
        with open(out, "w", encoding="utf-8") as f:
            f.write(new)
    return len(items), not same


def main():
    token = os.environ.get("VK_TOKEN")
    owners = os.environ.get("VK_OWNER_IDS") or os.environ.get("VK_OWNER_ID") or str(DEFAULT_OWNER)
    try:
        n, changed = update_repeats(token, ROOT, owners, int(os.environ.get("REPEATS_LIMIT", "48")))
    except RuntimeError as e:
        sys.exit(str(e))
    print("repeats.json updated: %d items" % n if changed else "no changes")


if __name__ == "__main__":
    main()
