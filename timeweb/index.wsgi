# Стартовый файл сайта для хостинга Timeweb.
# Лежит в папке сайта public_html и запускает app.py из папки ~/wedding-site.
import glob
import os
import sys
import traceback

# Пароль для страницы ответов гостей: /admin?key=ПАРОЛЬ
os.environ.setdefault('ADMIN_KEY', 'liza-vanya-2026')
# Telegram (необязательно): уберите # и впишите свои значения
# os.environ['TG_BOT_TOKEN'] = '123456:ABC...'
# os.environ['TG_CHAT_ID'] = '-1001234567890'

try:
    # Ищем домашнюю папку: поднимаемся от public_html, пока не найдём wedding-site и venv
    here = os.path.dirname(os.path.abspath(__file__))
    home = here
    while home != '/' and not (os.path.isdir(os.path.join(home, 'wedding-site')) and os.path.isdir(os.path.join(home, 'venv'))):
        home = os.path.dirname(home)

    ver = 'python%d.%d' % sys.version_info[:2]
    for sp in glob.glob(os.path.join(home, 'venv', 'lib', ver, 'site-packages')):
        sys.path.insert(0, sp)
    sys.path.insert(0, os.path.join(home, 'wedding-site'))

    from app import app as application  # noqa: E402
except Exception:
    _err = 'Сайт не запустился.\n\nPython: %s\nФайл: %s\n\n%s' % (sys.version, __file__, traceback.format_exc())

    def application(environ, start_response):
        start_response('200 OK', [('Content-Type', 'text/plain; charset=utf-8')])
        return [_err.encode('utf-8')]
