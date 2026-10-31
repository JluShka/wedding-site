"""
Сайт-приглашение «Ванечка & Елизаветик» + приём ответов анкеты.

Что делает:
  /                 — показывает приглашение (static/index.html)
  /api/rsvp         — принимает ответ гостя (POST) и сохраняет в базу rsvp.db
  /api/rsvp/<id>    — отдаёт гостю его прошлый ответ, чтобы он мог его поправить
  /admin?key=...    — таблица всех ответов с итогами (только для вас)
  /admin/export.csv?key=...  — скачать ответы в CSV (открывается в Excel и Google Таблицах)

Настройки берутся из переменных окружения (см. README.md):
  ADMIN_KEY     — пароль для страницы /admin (обязательно поменяйте!)
  TG_BOT_TOKEN  — токен Telegram-бота (необязательно)
  TG_CHAT_ID    — id группы, куда бот пишет ответы (необязательно)
"""

import csv
import io
import json
import os
import sqlite3
import urllib.parse
import urllib.request
from datetime import datetime, timezone, timedelta
from html import escape

from flask import Flask, Response, abort, g, jsonify, request, send_from_directory

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATIC_DIR = os.path.join(BASE_DIR, "static")
DB_PATH = os.environ.get("DB_PATH", os.path.join(BASE_DIR, "rsvp.db"))

ADMIN_KEY = os.environ.get("ADMIN_KEY", "change-me")
TG_BOT_TOKEN = os.environ.get("TG_BOT_TOKEN", "")
TG_CHAT_ID = os.environ.get("TG_CHAT_ID", "")

MSK = timezone(timedelta(hours=3))

ATTEND_OPTIONS = {"Конечно да!", "К сожалению, нет", "Дам ответ чуть позже"}
DRINK_OPTIONS = ["Безалкогольные", "Шампанское", "Вино белое", "Вино красное", "Крепкие напитки", "Неважно"]

app = Flask(__name__, static_folder=None)


# ---------- база данных ----------

def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(DB_PATH)
        g.db.row_factory = sqlite3.Row
    return g.db


@app.teardown_appcontext
def close_db(_exc):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db():
    with sqlite3.connect(DB_PATH) as db:
        db.execute(
            """
            CREATE TABLE IF NOT EXISTS rsvp (
                guest_id   TEXT PRIMARY KEY,
                name       TEXT NOT NULL,
                attend     TEXT NOT NULL,
                drinks     TEXT NOT NULL,   -- JSON-список
                comment    TEXT NOT NULL DEFAULT '',
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
            """
        )


init_db()


# ---------- Telegram ----------

def notify_telegram(row: dict, is_update: bool) -> None:
    """Отправляет ответ гостя в Telegram-группу. Если бот не настроен — ничего не делает."""
    if not (TG_BOT_TOKEN and TG_CHAT_ID):
        return
    icon = {"Конечно да!": "✅", "К сожалению, нет": "❌"}.get(row["attend"], "🤔")
    lines = [
        f"{icon} {'Гость изменил ответ' if is_update else 'Новый ответ'}",
        f"Имя: {row['name']}",
        f"Присутствие: {row['attend']}",
        f"Напитки: {', '.join(row['drinks']) or 'не выбрано'}",
    ]
    if row["comment"]:
        lines.append(f"Комментарий: {row['comment']}")
    data = urllib.parse.urlencode({"chat_id": TG_CHAT_ID, "text": "\n".join(lines)}).encode()
    url = f"https://api.telegram.org/bot{TG_BOT_TOKEN}/sendMessage"
    try:
        urllib.request.urlopen(url, data=data, timeout=8)
    except Exception as exc:  # ответ гостя уже сохранён, поэтому просто пишем в лог
        app.logger.warning("Telegram не ответил: %s", exc)


# ---------- страницы сайта ----------

@app.get("/")
def index():
    return send_from_directory(STATIC_DIR, "index.html")


@app.get("/<path:filename>")
def static_files(filename):
    return send_from_directory(STATIC_DIR, filename)


# ---------- API анкеты ----------

def clean_text(value, limit):
    return str(value or "").strip()[:limit]


@app.post("/api/rsvp")
def save_rsvp():
    data = request.get_json(silent=True) or {}
    guest_id = clean_text(data.get("guest_id"), 64)
    name = clean_text(data.get("name"), 120)
    attend = clean_text(data.get("attend"), 40)
    comment = clean_text(data.get("comment"), 500)
    drinks = [d for d in (data.get("drinks") or []) if d in DRINK_OPTIONS]

    if not guest_id or not name:
        return jsonify(error="Нужно указать имя"), 400
    if attend not in ATTEND_OPTIONS:
        return jsonify(error="Неизвестный вариант ответа"), 400

    now = datetime.now(MSK).strftime("%Y-%m-%d %H:%M")
    db = get_db()
    existed = db.execute("SELECT 1 FROM rsvp WHERE guest_id = ?", (guest_id,)).fetchone() is not None
    db.execute(
        """
        INSERT INTO rsvp (guest_id, name, attend, drinks, comment, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(guest_id) DO UPDATE SET
            name = excluded.name, attend = excluded.attend, drinks = excluded.drinks,
            comment = excluded.comment, updated_at = excluded.updated_at
        """,
        (guest_id, name, attend, json.dumps(drinks, ensure_ascii=False), comment, now, now),
    )
    db.commit()

    notify_telegram({"name": name, "attend": attend, "drinks": drinks, "comment": comment}, existed)
    return jsonify(ok=True)


@app.get("/api/rsvp/<guest_id>")
def get_rsvp(guest_id):
    row = get_db().execute("SELECT * FROM rsvp WHERE guest_id = ?", (guest_id[:64],)).fetchone()
    if row is None:
        abort(404)
    return jsonify(
        name=row["name"], attend=row["attend"], drinks=json.loads(row["drinks"]), comment=row["comment"]
    )


# ---------- админка ----------

def require_admin():
    if request.args.get("key") != ADMIN_KEY or ADMIN_KEY == "change-me":
        abort(403)


def all_rows():
    rows = get_db().execute("SELECT * FROM rsvp ORDER BY created_at").fetchall()
    return [dict(r, drinks=json.loads(r["drinks"])) for r in rows]


@app.get("/admin")
def admin():
    require_admin()
    rows = all_rows()
    yes = sum(r["attend"] == "Конечно да!" for r in rows)
    no = sum(r["attend"] == "К сожалению, нет" for r in rows)
    later = len(rows) - yes - no
    drink_counts = {d: sum(d in r["drinks"] for r in rows if r["attend"] == "Конечно да!") for d in DRINK_OPTIONS}

    body_rows = "".join(
        f"<tr><td>{escape(r['name'])}</td><td>{escape(r['attend'])}</td>"
        f"<td>{escape(', '.join(r['drinks']))}</td><td>{escape(r['comment'])}</td>"
        f"<td>{escape(r['updated_at'])}</td></tr>"
        for r in rows
    ) or '<tr><td colspan="5">Пока никто не ответил</td></tr>'
    drinks_html = "".join(f"<li>{escape(d)}: <b>{n}</b></li>" for d, n in drink_counts.items())
    key = urllib.parse.quote(ADMIN_KEY)

    return f"""<!doctype html><html lang="ru"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>Ответы гостей</title>
<style>
body{{font-family:system-ui,sans-serif;background:#FBF4EA;color:#1E1416;margin:0;padding:24px 16px}}
.w{{max-width:1000px;margin:0 auto}} h1{{color:#6F0D1C;margin:0 0 16px}}
.t{{display:flex;flex-wrap:wrap;gap:8px;margin-bottom:16px}}
.t span{{background:#fff;border-radius:999px;padding:6px 14px;font-weight:700;color:#6F0D1C}}
.scroll{{overflow-x:auto;background:#fff;border-radius:14px}}
table{{border-collapse:collapse;width:100%;min-width:640px}}
th,td{{text-align:left;padding:10px 12px;border-bottom:1px solid #F4E8D7;vertical-align:top}}
th{{background:#6F0D1C;color:#FBF4EA;font-weight:600}}
a.btn{{display:inline-block;margin:16px 0;background:#6F0D1C;color:#FBF4EA;padding:10px 18px;border-radius:999px;text-decoration:none}}
</style></head><body><div class="w">
<h1>Ответы гостей</h1>
<div class="t"><span>Всего: {len(rows)}</span><span>Придут: {yes}</span><span>Не смогут: {no}</span><span>Думают: {later}</span></div>
<p><b>Напитки (у тех, кто придёт):</b></p><ul>{drinks_html}</ul>
<div class="scroll"><table><tr><th>Имя</th><th>Присутствие</th><th>Напитки</th><th>Комментарий</th><th>Обновлено</th></tr>{body_rows}</table></div>
<a class="btn" href="/admin/export.csv?key={key}">Скачать CSV для Excel / Google Таблиц</a>
</div></body></html>"""


@app.get("/admin/export.csv")
def export_csv():
    require_admin()
    buf = io.StringIO()
    buf.write("﻿")  # чтобы Excel правильно показал русские буквы
    writer = csv.writer(buf, delimiter=";")
    writer.writerow(["Имя", "Присутствие", "Напитки", "Комментарий", "Первый ответ", "Обновлено"])
    for r in all_rows():
        writer.writerow([r["name"], r["attend"], ", ".join(r["drinks"]), r["comment"], r["created_at"], r["updated_at"]])
    return Response(
        buf.getvalue(),
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment; filename=otvety-gostey.csv"},
    )


if __name__ == "__main__":
    # Локальный запуск: python app.py → открыть http://127.0.0.1:5000
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)), debug=False)
