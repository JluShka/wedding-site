#!/bin/bash
# Установка сайта на хостинг Timeweb. Запуск: bash ~/wedding-site/timeweb/setup.sh
set -e
cd ~
echo "1/4 Создаю окружение Python..."
if [ ! -d venv ]; then
  PYV=$(python3 -c 'import sys;print(f"{sys.version_info[0]}.{sys.version_info[1]}")')
  wget -q "https://bootstrap.pypa.io/virtualenv/$PYV/virtualenv.pyz" -O virtualenv.pyz
  python3 virtualenv.pyz venv
  rm -f virtualenv.pyz
fi
echo "2/4 Устанавливаю Flask..."
venv/bin/pip install -q -r wedding-site/requirements.txt
echo "3/4 Ищу папку сайта..."
SITE=$(find ~ -maxdepth 3 -type d -name public_html -not -path '*/wedding-site/*' | head -1)
if [ -z "$SITE" ]; then echo "Не нашла папку public_html — пришлите скриншот команды: ls ~"; exit 1; fi
echo "   Папка сайта: $SITE"
mkdir -p ~/old_site_backup
for f in index.html index.htm index.php; do [ -f "$SITE/$f" ] && mv "$SITE/$f" ~/old_site_backup/ || true; done
cp ~/wedding-site/timeweb/index.wsgi "$SITE/index.wsgi"
cp ~/wedding-site/timeweb/.htaccess "$SITE/.htaccess"
chmod 755 "$SITE/index.wsgi"
echo "4/4 Проверяю, что сайт запускается..."
~/venv/bin/python -c "import runpy; runpy.run_path('$SITE/index.wsgi'); print('   Всё работает!')"
echo "Готово. Откройте адрес сайта в браузере."
