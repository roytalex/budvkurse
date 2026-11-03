# Docker и постоянная ссылка ngrok

На этом ПК перенос завершён 3 ноября 2026: контейнеры запущены, перезапуск Docker проверен. Повторно переносить старую базу не нужно. Результаты и оставшиеся проверки MAX — в [RELEASE-CHECK.md](RELEASE-CHECK.md).

Проект запускается на твоём ПК: PostgreSQL, сайт с API и ботом MAX, ngrok. Бот и отправка напоминаний работают внутри контейнера `app`.

Закреплённый адрес аккаунта: https://imply-suitable-safari.ngrok-free.dev/?max=1

## Первый запуск

1. Установи и открой Docker Desktop с Linux containers / WSL 2. Если установщик требует перезагрузки Windows, сохрани работу и перезагрузи ПК. Дождись запуска Docker Engine.
2. В корневом `.env.ngrok` заполни `NGROK_AUTHTOKEN`: нажми **Show authtoken** в панели ngrok и вставь сам токен, а не команду. Остальные значения уже подготовлены локально. Токен MAX и токен ngrok разные. `.env.ngrok` исключён из Git и образа Docker.
3. Перед переходом перенеси существующую базу и uploads по инструкции ниже. Затем останови прежний Uvicorn на порту 4174, чтобы не запускать два обработчика напоминаний одновременно.
4. Открой `start-docker.cmd`. Для запуска вручную из корня проекта:

```powershell
docker compose --env-file .env.ngrok -f compose.ngrok.yaml up -d --build --wait
docker compose --env-file .env.ngrok -f compose.ngrok.yaml ps
```

5. Проверь `http://127.0.0.1:4174/health` и `https://imply-suitable-safari.ngrok-free.dev/health`: ответ должен быть `{"status":"ok"}`. Проверяй публичную ссылку отдельно: состояние контейнера ngrok `running` само по себе не подтверждает открытый туннель.
6. Подключи доставку событий боту:

```powershell
docker compose --env-file .env.ngrok -f compose.ngrok.yaml exec app python -m scripts.setup_max --register
```

После успешной проверки попроси организатора сохранить адрес мини-приложения в настройках бота MAX. При повторном запуске тот же адрес используется явно; новый случайный домен не создаётся. Бесплатный ngrok может показывать промежуточную страницу перед сайтом. Открытие внутри MAX нужно проверить отдельно на телефоне.

## Работа после перезагрузки

В Docker Desktop → Settings → General включи **Start Docker Desktop when you sign in to your computer**. Контейнеры имеют `restart: unless-stopped`: после запуска Docker они поднимутся снова, если ты не остановил их вручную. После ручной остановки запусти `start-docker.cmd`.

Пока компьютер спит, выключен, не подключён к интернету или Docker закрыт, сайт и бот недоступны. Адрес при этом остаётся закреплённым за аккаунтом. Это не круглосуточный облачный хостинг. Лимиты и состояние аккаунта ngrok также влияют на доступность.

## Данные и перенос

Именованные тома `budvkurse-ngrok_database` и `budvkurse-ngrok_uploads` сохраняют базу и фотографии при перезапуске и пересоздании контейнеров. Не выполняй `docker compose down -v`: эта команда удаляет тома с данными. Прежняя Windows-база не подключается к новой автоматически и не удаляется.

Перед переносом останови запись через прежний сервер и сделай `pg_dump` именно базы `budvkurse_app` в custom format без владельцев и прав; сохрани папку `beckend/uploads`. Пароль передавай через окружение `PGPASSWORD`, не добавляй в командную строку или Git. Сначала запусти только `db`, восстанови копию в пустую базу командой `pg_restore --no-owner --no-acl --exit-on-error -U budvkurse -d budvkurse_app`. Не накатывай копию поверх уже заполненной базы. Создай контейнер `app`, скопируй uploads в `/app/beckend/uploads`, проверь владельца каталога (`app`) и сравни количество записей и файлы с исходником. Затем запусти `app` и `ngrok`. Миграции выполняются перед стартом приложения.

Для резервной копии контейнерной базы без двоичного перенаправления PowerShell:

```powershell
docker compose --env-file .env.ngrok -f compose.ngrok.yaml exec -T db pg_dump -U budvkurse -d budvkurse_app -Fc --no-owner --no-acl -f /tmp/budvkurse.dump
docker compose --env-file .env.ngrok -f compose.ngrok.yaml cp db:/tmp/budvkurse.dump ./budvkurse.dump
```

Сохраняй отдельную копию uploads и ключей `.env.ngrok` в приватном месте. Дамп базы исключён из Git.

## Обновления и диагностика

После изменения кода запусти `start-docker.cmd` повторно: образ приложения пересоберётся. Не запускай параллельно старый `start.cmd` или Uvicorn. Локальная база Windows может продолжать работать для других проектов; контейнерная БД не занимает порт 5432 хоста.

```powershell
docker compose --env-file .env.ngrok -f compose.ngrok.yaml logs --tail=60 app ngrok
docker compose --env-file .env.ngrok -f compose.ngrok.yaml config --quiet
```

Не публикуй полный вывод `docker compose config` или `docker inspect`: в них могут находиться ключи. Журналы контейнеров ограничены по объёму. Инспектор HTTP-запросов ngrok отключён, а порт приложения опубликован только на `127.0.0.1`. Токены не встраиваются в Docker-образ.
