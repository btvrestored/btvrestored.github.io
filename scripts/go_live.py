#!/usr/bin/env python3
"""Запускает «Сейчас в эфире»: кладёт в tracklist.json эфир и момент старта.

    python3 scripts/go_live.py episodes/ep01.json            # старт = сейчас
    python3 scripts/go_live.py episodes/ep01.json --offset 15 # учесть задержку VK Live (сек): трек на сайте позже на 15 с
    python3 scripts/go_live.py --idle                         # в OBS включён idle: виджет показывает «ожидание эфира»
    python3 scripts/go_live.py --stop                         # убрать виджет
Добавьте --push, чтобы сразу сделать git commit и push (сайт обновится через ~1 минуту).
Запускайте в момент, когда в OBS реально стартует первый файл эфира.
"""
import argparse, datetime, json, subprocess, os

ap = argparse.ArgumentParser()
ap.add_argument("episode", nargs="?")
ap.add_argument("--offset", type=float, default=0)
ap.add_argument("--stop", action="store_true", help="скрыть виджет")
ap.add_argument("--idle", action="store_true", help="показывать «ожидание эфира» (в OBS идёт idle-файл)")
ap.add_argument("--at", default="", help="запланированный старт, например \"2026-10-06 20:00\" (местное время); до него виджет показывает ожидание и отсчёт")
ap.add_argument("--push", action="store_true")
a = ap.parse_args()
root = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
out = os.path.join(root, "tracklist.json")
if a.idle:
    data = {"idle": True, "start": None, "tracks": []}
elif a.stop or not a.episode:
    data = {"start": None, "tracks": []}
else:
    ep = json.load(open(a.episode, encoding="utf-8"))
    if a.at:
        st = datetime.datetime.fromisoformat(a.at.replace(" ", "T")).astimezone(datetime.timezone.utc)
    else:
        st = datetime.datetime.now(datetime.timezone.utc)
    data = {"start": st.isoformat(timespec="seconds"), "offset": a.offset, "title": ep.get("title", ""), "tracks": ep["tracks"]}
    if ep.get("duration") is not None:
        data["end"] = ep["duration"]
json.dump(data, open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("tracklist.json:", "ожидание (idle)" if data.get("idle") else ("старт " + data["start"] if data["start"] else "остановлен"))
if a.push:
    subprocess.run(["git", "-C", root, "add", "tracklist.json"], check=True)
    subprocess.run(["git", "-C", root, "commit", "-m", "Tracklist: " + ("go live" if data["start"] else "idle" if data.get("idle") else "stop")], check=True)
    subprocess.run(["git", "-C", root, "push"], check=True)
