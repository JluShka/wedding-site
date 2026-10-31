#!/bin/bash
# Установка/обновление сайта на хостинге Timeweb.
# Запуск: cd ~/wedding-site && git pull && bash timeweb/setup.sh
set -e
cd ~
echo "1/4 Готовлю установщик пакетов..."
if [ ! -x venv/bin/pip ]; then
  rm -rf venv
  PYV=$(python3 -c 'import sys;print(f"{sys.version_info[0]}.{sys.version_info[1]}")')
  wget -q "https://bootstrap.pypa.io/virtualenv/$PYV/virtualenv.pyz" -O virtualenv.pyz
  python3 virtualenv.pyz venv
  rm -f virtualenv.pyz
fi
echo "2/4 Ищу папку сайта..."
SITE=$(find ~ -maxdepth 3 -type d -name public_html -not -path '*/wedding-site/*' -not -path '*/.app/*' | head -1)
if [ -z "$SITE" ]; then echo "Не нашла папку public_html — пришлите скриншот команды: ls ~"; exit 1; fi
echo "   Папка сайта: $SITE"
APP="$SITE/.app"
echo "3/4 Копирую сайт и ставлю Flask в $APP ..."
mkdir -p "$APP"
cp ~/wedding-site/app.py ~/wedding-site/requirements.txt "$APP/"
rm -rf "$APP/static" && cp -r ~/wedding-site/static "$APP/static"
rm -rf "$APP/lib"
~/venv/bin/pip install -q --target "$APP/lib" -r ~/wedding-site/requirements.txt
# перенос ответов гостей из старой установки, если были
[ -f ~/wedding-site/rsvp.db ] && [ ! -f "$APP/rsvp.db" ] && mv ~/wedding-site/rsvp.db "$APP/rsvp.db" || true
mkdir -p ~/old_site_backup
for f in index.html index.htm index.php; do [ -f "$SITE/$f" ] && mv "$SITE/$f" ~/old_site_backup/ || true; done
cp ~/wedding-site/timeweb/index.wsgi "$SITE/index.wsgi"
cp ~/wedding-site/timeweb/.htaccess "$SITE/.htaccess"
chmod 755 "$SITE/index.wsgi"
echo "4/4 Проверяю, что сайт запускается..."
python3 -c "import runpy; g=runpy.run_path('$SITE/index.wsgi'); assert g['application'].__module__!='__main__' and hasattr(g['application'],'test_client'), 'ошибка запуска'; print('   Всё работает!')"
echo "Готово. Откройте адрес сайта в браузере."
