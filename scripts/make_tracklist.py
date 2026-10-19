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

Режим «нарезка» (EDL без маркеров, обычный экспорт таймлинии: Timeline → Export → AAF/XML/EDL → «EDL-файлы»):
    скрипт берёт имена клипов (FROM CLIP NAME) и их время начала на таймлинии. Клипы короче --min-track (30 с)
    считаются заставками/склейками и пропускаются (на сайте остаётся предыдущий трек). Служебные клипы можно
    назначить правилами --rules rules.json, например: [["Рекламный блок|adsstart", "ad"], ["EBU Color", "tech"]].
    Виды: ad, promo, wait, tech, skip (пропустить), music (принудительно трек). Имена очищаются от «(1080P_HD)», «(Official Video)» и т. п.

Текстовый формат (одна строка — один трек):
    00:00:00 Артист — Название
    00:03:41 Артист 2 — Название 2

Использование:
    python3 scripts/make_tracklist.py markers.edl episodes/ep01.json [--fps 25] [--start-tc 01:00:00:00] [--title "Эфир 1"]
"""
import argparse, json, re, sys

def tc_to_str(sec):
    sec = int(sec); return "%d:%02d:%02d" % (sec // 3600, sec % 3600 // 60, sec % 60)

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

DEFAULT_RULES = [(r"рекламн|adsstart|\bads?\b", "ad")]
JUNK = re.compile(r"[\[(][^\])]*\b(official|hd|4k|video|music|audio|lyric|lyrics|clip|version|\d{3,4}p(_hd)?)\b[^\])]*[\])]", re.I)

def clean_clip_name(n):
    n = re.sub(r"\.(mp4|mov|mkv|avi|webm|png|jpg|mxf|wav|mp3)$", "", n.strip(), flags=re.I)
    for _ in range(3): n = JUNK.sub("", n)
    if not re.search(r" [-–—] ", n): n = re.sub(r"_\s", " - ", n, count=1)   # «Metallica_ Nothing…» → «Metallica - Nothing…»
    n = re.sub(r"_\s", ": ", n)            # «O Come_ O Come» → «O Come: O Come»
    n = re.sub(r"\s+", " ", n).strip(" -–—")
    return n

def parse_cutlist(text, fps, min_track, rules):
    """Возвращает [(rec_in, name, kind_or_None, длительность_с)] по обычному EDL-экспорту таймлинии."""
    lines = text.splitlines()
    ev = re.compile(r"^\s*(\d+)\s+(\S+)\s+(\S+)\s+(\S+)(?:\s+(\d+))?\s+(\d\d:\d\d:\d\d[:;]\d\d)\s+(\d\d:\d\d:\d\d[:;]\d\d)\s+(\d\d:\d\d:\d\d[:;]\d\d)\s+(\d\d:\d\d:\d\d[:;]\d\d)")
    out, report = [], []
    for i, ln in enumerate(lines):
        m = ev.match(ln)
        if not m: continue
        rin, rout = m.group(8), m.group(9)
        dur = tc_to_sec(rout, fps) - tc_to_sec(rin, fps)
        if dur <= 0: continue
        frm = to = ""
        for nxt in lines[i+1:i+4]:
            if re.match(r"^\s*\d+\s", nxt): break
            a = re.match(r"^\*\s*FROM CLIP NAME:\s*(.+?)\s*$", nxt)
            b = re.match(r"^\*\s*TO CLIP NAME:\s*(.+?)\s*$", nxt)
            if a: frm = a.group(1)
            if b: to = b.group(1)
        raw = to if (frm.lower() == "transition" and to) else frm
        if not raw: continue
        # переход: длительность записи события — это длительность перехода, реальная длина клипа неизвестна → считаем треком
        kind = None
        for pat, k in rules:
            if re.search(pat, raw, re.I): kind = k; break
        if kind == "skip": continue
        if kind is None and dur < min_track and not (frm.lower() == "transition"):
            continue
        out.append((rin, raw, kind, dur))
    # склеиваем подряд идущие события одного клипа (разрезы, концы переходов)
    merged = []
    for rin, raw, kind, dur in out:
        if merged and merged[-1][1] == raw: continue
        merged.append((rin, raw, kind, dur))
    return merged

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
ap.add_argument("--min-track", type=float, default=30, help="режим нарезки: клипы короче N секунд считаются заставками и пропускаются")
ap.add_argument("--rules", default="", help="JSON со списком правил [[\"regex\", \"ad|promo|wait|tech|skip|music\"], ...]")
ap.add_argument("--duration", default="", help="длительность эфира (ЧЧ:ММ:СС), после неё сайт снова покажет ожидание")
a = ap.parse_args()

text = open(a.src, encoding="utf-8-sig", errors="replace").read()
is_edl = bool(re.search(r"^\s*TITLE:|^\s*FCM:|\|M:", text, re.M))
cut_mode = is_edl and not re.search(r"\|M:", text)
rows = []
if cut_mode:
    rules = list(DEFAULT_RULES)
    if a.rules: rules = [tuple(r) for r in json.load(open(a.rules, encoding="utf-8"))] + rules
    cuts = parse_cutlist(text, a.fps, a.min_track, rules)
    if not cuts: sys.exit("В EDL не найдено клипов")
    print("Режим «нарезка»: маркеров нет, беру имена клипов (%d шт.)" % len(cuts))
    rows = []
    for rin, raw, kind, dur in cuts:
        if kind in ("ad", "promo", "wait", "tech"):
            rows.append((rin, "[%s]" % kind))
        else:
            rows.append((rin, clean_clip_name(raw)))
    rows = [r for i, r in enumerate(rows) if not (i and r[1] == rows[i-1][1] and r[1].startswith("["))]   # подряд идущие «реклама» → один блок
elif is_edl:
    rows = parse_edl(text, a.fps)
else:
    rows = parse_txt(text)
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
for tr in tracks:
    if "kind" in tr: continue
    if not tr["artist"] or re.fullmatch(r"[\d\W_]+", tr["title"]):
        print("⚠ проверьте имя (%s): «%s — %s»" % (tc_to_str(tr["t"]), tr["artist"], tr["title"]))
out = {"title": a.title, "tracks": tracks}
if a.duration: out["duration"] = tc_to_sec(a.duration, a.fps)
elif cut_mode:
    ends = [tc_to_sec(m.group(9), a.fps) for m in re.finditer(r"^\s*\d+\s+\S+\s+\S+\s+\S+(?:\s+\d+)?\s+\S+\s+\S+\s+(\S+)\s+(\S+)", text, re.M)] if False else []
    last = re.findall(r"(\d\d:\d\d:\d\d[:;]\d\d)\s*$", text, re.M)
    if last: out["duration"] = round(max(tc_to_sec(x, a.fps) for x in last) - base, 2)
json.dump(out, open(a.dst, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("%d треков → %s" % (len(tracks), a.dst))
