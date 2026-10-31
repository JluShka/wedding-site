# Сайт-приглашение «Ванечка & Елизаветик»

В папке:
- `app.py` — сервер на Python (Flask): показывает сайт и принимает ответы анкеты
- `static/` — сама страница и картинки
- `requirements.txt` — что установить

Ответы сохраняются в файл `rsvp.db` рядом с `app.py`. Отвечать могут все гости, без регистрации.
Если гость ответит ещё раз с того же телефона, его ответ обновится, а не задвоится.

---

## 1. Проверить у себя на компьютере

```bash
pip install -r requirements.txt
python app.py
```

Открой http://127.0.0.1:5000 — это сайт.
Ответы: http://127.0.0.1:5000/admin?key=ТВОЙ_ПАРОЛЬ (пароль задаётся в `ADMIN_KEY`, см. ниже).

На Windows пароль задаётся так: `set ADMIN_KEY=мой-пароль` перед `python app.py`,
на Mac/Linux: `ADMIN_KEY=мой-пароль python app.py`.

---

## 2. Выложить в интернет бесплатно — PythonAnywhere

Подходит лучше всего: бесплатно, файл с ответами не пропадает.

1. Зарегистрируйся на https://www.pythonanywhere.com (бесплатный аккаунт «Beginner»).
   Адрес сайта будет `https://ИМЯ.pythonanywhere.com` — выбери имя покрасивее, например `vanya-liza`.
2. Вкладка **Files** → создай папку `wedding-site` и загрузи туда `app.py`, `requirements.txt`
   и папку `static` со всеми файлами (кнопка Upload a file; папку `static` создай и загрузи файлы внутрь).
3. Вкладка **Web** → **Add a new web app** → **Manual configuration** → **Python 3.10** (или новее).
4. На той же странице найди **WSGI configuration file**, открой его, удали всё и вставь:

   ```python
   import os, sys
   path = '/home/ИМЯ/wedding-site'          # ИМЯ — твой логин на PythonAnywhere
   if path not in sys.path:
       sys.path.insert(0, path)

   os.environ['ADMIN_KEY'] = 'придумай-длинный-пароль'
   # Telegram (необязательно, см. раздел 3):
   # os.environ['TG_BOT_TOKEN'] = '123456:ABC...'
   # os.environ['TG_CHAT_ID'] = '-1001234567890'

   from app import app as application
   ```
5. Нажми зелёную кнопку **Reload**. Сайт открыт по адресу `https://ИМЯ.pythonanywhere.com`.
6. Ответы гостей: `https://ИМЯ.pythonanywhere.com/admin?key=твой-пароль`.
   Там же кнопка «Скачать CSV» — файл открывается в Excel и импортируется в Google Таблицы
   (Файл → Импорт → Загрузка).

Важно: на бесплатном тарифе PythonAnywhere раз в 3 месяца просит нажать кнопку
«Run until 3 months from today» на вкладке Web — до свадьбы это не понадобится.

---

## 3. Ответы в Telegram-группу (по желанию)

1. В Telegram открой **@BotFather** → `/newbot` → придумай название и имя бота.
   BotFather пришлёт **токен** вида `123456789:AA...` — это `TG_BOT_TOKEN`.
2. Добавь бота в вашу группу и напиши в группе любое сообщение, например «привет».
3. Открой в браузере `https://api.telegram.org/botТОКЕН/getUpdates` (вставь свой токен).
   Найди `"chat":{"id":-100...` — это число с минусом и есть `TG_CHAT_ID`.
   Если там пусто — в @BotFather сделай `/setprivacy` → выбери бота → **Disable**, и снова напиши в группу.
4. Впиши оба значения в WSGI-файл (уберите `#` в начале строк) и нажми **Reload**.

Теперь каждый новый ответ гостя будет приходить в группу сообщением:

```
✅ Новый ответ
Имя: Иван Иванов
Присутствие: Конечно да!
Напитки: Шампанское, Вино красное
Комментарий: буду с тортом
```

---

## Как поменять текст на сайте

Всё на странице — в файле `static/index.html`. Отредактируй его, загрузи заново в Files
и нажми **Reload** на вкладке Web.

---

## Timeweb (открывается в России без VPN)

1. В панели Timeweb на главной странице, в блоке «Статус сервисов», включи SSH.
2. Открой раздел **SSH-консоль** и выполни:
   ```bash
   cd ~ && git clone https://github.com/JluShka/wedding-site.git && bash wedding-site/timeweb/setup.sh
   ```
3. Пароль от страницы ответов меняется в файле `public_html/index.wsgi` (строка с `ADMIN_KEY`).
4. Сайт ставится в скрытую папку `public_html/.app` (веб-сервер Timeweb видит только папку сайта), ответы гостей — в `public_html/.app/rsvp.db`. Обновить сайт после изменений: `cd ~/wedding-site && git pull && bash timeweb/setup.sh`.
