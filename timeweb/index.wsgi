# Стартовый файл сайта для хостинга Timeweb.
# Лежит в папке сайта public_html и запускает app.py из папки ~/wedding-site.
import glob
import os
import sys

# Пароль для страницы ответов гостей: /admin?key=ПАРОЛЬ
os.environ.setdefault('ADMIN_KEY', 'liza-vanya-2026')
# Telegram (необязательно): уберите # и впишите свои значения
# os.environ['TG_BOT_TOKEN'] = '123456:ABC...'
# os.environ['TG_CHAT_ID'] = '-1001234567890'

# Ищем домашнюю папку: поднимаемся от public_html, пока не найдём wedding-site и venv
here = os.path.dirname(os.path.abspath(__file__))
home = here
while home != '/' and not (os.path.isdir(os.path.join(home, 'wedding-site')) and os.path.isdir(os.path.join(home, 'venv'))):
    home = os.path.dirname(home)

for sp in glob.glob(os.path.join(home, 'venv', 'lib', 'python3*', 'site-packages')):
    sys.path.insert(0, sp)
sys.path.insert(0, os.path.join(home, 'wedding-site'))

from app import app as application  # noqa: E402
