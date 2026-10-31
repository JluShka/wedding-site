# Стартовый файл сайта для хостинга Timeweb.
# Лежит в public_html; сам сайт установлен в скрытую папку public_html/.app
# (веб-сервер Timeweb видит только папку сайта).
import os
import sys
import traceback

# Пароль для страницы ответов гостей: /admin?key=ПАРОЛЬ
os.environ.setdefault('ADMIN_KEY', 'liza-vanya-2026')
# Telegram (необязательно): уберите # и впишите свои значения
# os.environ['TG_BOT_TOKEN'] = '123456:ABC...'
# os.environ['TG_CHAT_ID'] = '-1001234567890'

APP_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.app')
sys.path.insert(0, os.path.join(APP_DIR, 'lib'))
sys.path.insert(0, APP_DIR)

try:
    from app import app as application  # noqa: E402
except Exception:
    _diag = []
    for _d in (APP_DIR, os.path.join(APP_DIR, 'lib')):
        try:
            _diag.append('%s -> %s' % (_d, sorted(os.listdir(_d))[:20]))
        except Exception as _e:
            _diag.append('%s -> ОШИБКА %r' % (_d, _e))
    _err = 'Сайт не запустился.\n\nPython: %s\n\n%s\n\n%s' % (sys.version, traceback.format_exc(), '\n'.join(_diag))

    def application(environ, start_response):
        start_response('200 OK', [('Content-Type', 'text/plain; charset=utf-8')])
        return [_err.encode('utf-8')]
