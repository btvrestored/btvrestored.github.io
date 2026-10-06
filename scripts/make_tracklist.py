#!/usr/bin/env python3
"""Превращает маркеры DaVinci Resolve (EDL) или текстовый список в файл эфира episodes/<имя>.json.

Resolve: расставьте маркеры на таймлинии (имя маркера = «Исполнитель — Название»),
затем File → Export → Timeline Markers to EDL… (насколько известно, пункт может называться чуть иначе в вашей версии).

Служебные блоки — имя маркера начинается с метки в квадратных скобках:
    [ожидание] / [wait]      ожидание начала эфира
    [реклама]  / [ad]        рекламный блок
    [заставки] / [promo]     заставки и анонсы
    [техника]  / [tech]      технические неполадки
После метки можно написать свой текст: «[tech] Ушли за кабелем». Без текста сайт покажет случайную шутку.

Текстовый формат (одна строка — один трек):
    00:00:00 Артист — Название
    00:03:41 Артист 2 — Название 2

Использование:
    python3 scripts/make_tracklist.py markers.edl episodes/ep01.json [--fps 25] [--start-tc 01:00:00:00] [--title "Эфир 1"]
"""
import argparse, json, re, sys

def tc_to_sec(tc, fps):
    p = re.split(r"[:;]", tc.strip())
    if len(p) == 4:
        h, m, s, f = map(int, p); return h*3600 + m*60 + s + f/fps
    if len(p) == 3:
        h, m, s = map(int, p); return h*3600 + m*60 + s
    if len(p) == 2:
        m, s = map(int, p); return m*60 + s
    raise ValueError("bad timecode: " + tc)

KINDS = {"wait": "wait", "ожидание": "wait", "ad": "ad", "реклама": "ad",
         "promo": "promo", "заставка": "promo", "заставки": "promo", "анонс": "promo", "анонсы": "promo",
         "tech": "tech", "техника": "tech", "неполадки": "tech", "пауза": "tech"}

def split_kind(name):
    """«[tech] текст» -> ("tech", "текст"); обычный трек -> (None, name)."""
    m = re.match(r"^\s*[\[#]\s*([^\]\s]+)\s*\]?\s*(.*)$", name)
    if m and m.group(1).lower() in KINDS:
        return KINDS[m.group(1).lower()], m.group(2).strip()
    return None, name

def split_name(name):
    for sep in (" — ", " – ", " - "):
        if sep in name:
            a, t = name.split(sep, 1); return a.strip(), t.strip()
    return "", name.strip()

def parse_edl(text, fps):
    out, lines = [], text.splitlines()
    ev = re.compile(r"^\s*\d+\s+\S+\s+\S+\s+\S+\s+(\S+)\s+(\S+)\s+(\S+)\s+(\S+)")
    for i, ln in enumerate(lines):
        m = ev.match(ln)
        if not m: continue
        rec_in = m.group(3)
        name = ""
        for nxt in lines[i+1:i+3]:
            mm = re.search(r"^(.*?)\|C:.*?\|M:(.*?)\s*\|D:", nxt)
            if mm:
                note, mname = mm.group(1).strip(), mm.group(2).strip()
                # имя маркера главное; если оно пустое или стандартное «Marker N» — берём заметку
                name = mname if mname and not re.match(r"^Marker \d+$", mname) else (note or mname)
                break
        if name: out.append((rec_in, name))
    return out

def parse_txt(text):
    out = []
    for ln in text.splitlines():
        m = re.match(r"^\s*(\d{1,2}(?::\d{2}){1,3}(?:;\d{2})?)\s+(.+?)\s*$", ln)
        if m: out.append((m.group(1), m.group(2)))
    return out

ap = argparse.ArgumentParser()
ap.add_argument("src"); ap.add_argument("dst")
ap.add_argument("--fps", type=float, default=25)
ap.add_argument("--start-tc", default="01:00:00:00", help="таймкод начала таймлинии (в Resolve по умолчанию 01:00:00:00)")
ap.add_argument("--title", default="")
ap.add_argument("--duration", default="", help="длительность эфира (ЧЧ:ММ:СС), после неё сайт снова покажет ожидание")
a = ap.parse_args()

text = open(a.src, encoding="utf-8-sig", errors="replace").read()
is_edl = bool(re.search(r"^\s*TITLE:|^\s*FCM:|\|M:", text, re.M))
rows = parse_edl(text, a.fps) if is_edl else parse_txt(text)
if not rows: sys.exit("Маркеры не найдены")
base = tc_to_sec(a.start_tc, a.fps) if is_edl else 0
tracks = []
for tc, name in rows:
    t = round(tc_to_sec(tc, a.fps) - base, 2)
    if t < 0: sys.exit("Отрицательное время у «%s» — проверьте --start-tc" % name)
    kind, rest = split_kind(name)
    if kind:
        tracks.append({"t": t, "kind": kind, "text": rest})      # служебный блок (пустой text — шутка по умолчанию)
    else:
        artist, title = split_name(name)
        tracks.append({"t": t, "artist": artist, "title": title})
tracks.sort(key=lambda x: x["t"])
out = {"title": a.title, "tracks": tracks}
if a.duration: out["duration"] = tc_to_sec(a.duration, a.fps)
json.dump(out, open(a.dst, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("%d треков → %s" % (len(tracks), a.dst))
