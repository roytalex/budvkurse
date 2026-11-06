# Будь в курсе — инструкция организаторам хакатона

Платформа школьных и городских мероприятий с мини-приложением MAX. Этот README — основная инструкция по развёртыванию, проверке и обслуживанию проекта.

## Что входит в проект

FastAPI, SQLAlchemy, Alembic и PostgreSQL; HTML/CSS/JavaScript, Leaflet и MapLibre. Папка сервера называется **beckend**. Бот работает через HTTP API MAX. Docker запускает API, сайт, миграции и фоновые уведомления.

Возможности: роли ученика и организатора, публикации и управление участниками, карта и календарь, избранное и планы, команды с заявками, отзывы, QR-подтверждение посещений, сертификаты, достижения, рейтинг участников и школ, челленджи и напоминания MAX. Организаторы не записываются на события. Администратор может удалять публикации и управлять справочниками.

## 1. Получение исходников



```powershell
git clone https://github.com/roytalex/budvkurse.git
cd budvkurse
```

Потребуется Docker Engine с Compose v2; на Windows — работающий Docker Desktop в режиме Linux-контейнеров. Python и PostgreSQL на хосте для Docker-запуска не нужны. Для frontend-тестов нужен Node.js.

Исходники не содержат рабочую базу, пароли, токены MAX/CloudPub и пользовательские загрузки. Новое развёртывание начинается с пустой базы. Получать реальные секреты нужно у владельца проекта или создавать собственные.

## 2. Быстрый локальный запуск без MAX

```powershell
Copy-Item .env.example .env
```

Открой `.env`. Замени `POSTGRES_PASSWORD` и `JWT_SECRET` на разные случайные значения. Для пароля БД используй латинские буквы и цифры без специальных URL-символов; для JWT — минимум 32 символа. Например, два раза выполни следующую команду и используй два разных результата:

```powershell
[guid]::NewGuid().ToString('N') + [guid]::NewGuid().ToString('N')
```

Поля MAX оставь пустыми. `DOMAIN` и `ACME_EMAIL` в локальной конфигурации не используются.

```powershell
docker compose --env-file .env -f compose.local.yaml up -d --build --wait
docker compose --env-file .env -f compose.local.yaml ps
```

Сайт: http://127.0.0.1:4174/ ; Swagger: http://127.0.0.1:4174/docs ; проверка БД/API: http://127.0.0.1:4174/health . Ожидается `{"status":"ok"}`. Миграции применяются при запуске app. Если порт занят, останови прежний экземпляр или измени левый порт в `compose.local.yaml`.

Создание первого администратора выполняется интерактивно:

```powershell
docker compose --env-file .env -f compose.local.yaml exec app python -m scripts.create_admin
```

Введи email, имя и пароль. Затем войди в приложение. Обычные ученики и организаторы регистрируются самостоятельно через форму; права администратора публичная регистрация не выдаёт.

## 3. Публичное размещение на сервере с доменом

Для независимости от домашнего ПК используй сервер с Docker, постоянным интернетом и доменом. Настрой DNS домена на IP сервера и открой входящие порты 80/443. В `.env` заполни `DOMAIN` (без https://), `ACME_EMAIL`, уникальные `POSTGRES_PASSWORD`, `JWT_SECRET` и при необходимости параметры MAX.

```sh
docker compose --env-file .env -f compose.yaml up -d --build --wait
docker compose --env-file .env -f compose.yaml exec app python -m scripts.create_admin
```

Конфигурация использует Caddy для HTTPS. Приложение доступно по `https://ваш-домен/`. Локальная, серверная и CloudPub-конфигурации используют отдельные Compose-проекты и тома: переход между ними сам по себе не переносит данные. Не запускай несколько экземпляров с одним ботом для обслуживания одного webhook.

## 4. CloudPub: публичный адрес для проекта на ПК

В текущей демонстрации используется https://kindly-competent-polecat.cloudpub.ru/ и бот https://max.ru/ideya_fiks_26_bot . Эти ресурсы принадлежат владельцу; новое развёртывание требует собственных доступов.

Создай **локальный** `.env.cloudpub` в корне с такими полями:

```dotenv
POSTGRES_PASSWORD=YOUR_RANDOM_DATABASE_PASSWORD
JWT_SECRET=YOUR_RANDOM_SECRET_AT_LEAST_32_CHARACTERS
CLOUDPUB_TOKEN=YOUR_CLOUDPUB_TOKEN
PUBLIC_BASE_URL=https://YOUR_ADDRESS.cloudpub.ru
MAX_BOT_TOKEN=YOUR_MAX_BOT_TOKEN
MAX_BOT_USERNAME=YOUR_BOT_NAME
MAX_WEBHOOK_SECRET=YOUR_RANDOM_WEBHOOK_SECRET_AT_LEAST_32_CHARACTERS
MAX_CA_BUNDLE=
```

Все значения YOUR_ нужно заменить. `MAX_BOT_USERNAME` — техническое имя бота, полученное от MAX, а не личный @username пользователя. Не публикуй этот файл и не вставляй токены в исходники.

```powershell
docker compose --env-file .env.cloudpub -f compose.cloudpub.yaml up -d --build --wait
docker compose --env-file .env.cloudpub -f compose.cloudpub.yaml logs --tail 50 cloudpub
```

Для первого подключения CloudPub укажи в `PUBLIC_BASE_URL` временное корректное HTTPS-значение, затем возьми выданный CloudPub адрес из панели или логов, впиши его вместо временного и повтори `up -d`. Только после этого регистрируй webhook. Не публикуй сырые логи без проверки на секреты. Туннель должен вести на `app:8000`. Сохраняй том `cloudpub-config`, иначе привязку адреса может потребоваться восстановить.

На существующем компьютере владельца достаточно запустить Docker Desktop и `start-docker.cmd`. Компьютер не должен выключаться или переходить в сон; Docker не делает размещение независимым от ПК.

## 5. Подключение мини-приложения и MAX

Заполни токен, имя бота, `PUBLIC_BASE_URL` и отдельный webhook-секрет. Для CloudPub:

```powershell
docker compose --env-file .env.cloudpub -f compose.cloudpub.yaml exec app python -m scripts.setup_max --register
```

Для серверного размещения замени параметры на `--env-file .env -f compose.yaml`. Команда настраивает webhook и команды; URL самого мини-приложения должен сохранить владелец настроек бота. Передай ему `https://ваш-адрес/?max=1`. Одной кнопки в сообщении недостаточно, если у бота настроен старый URL приложения.

Если API MAX требует дополнительный доверенный CA, создай `deploy/certs`, положи туда полученный из доверенного источника PEM и укажи `MAX_CA_BUNDLE=/app/certs/имя.pem`. Конфигурации CloudPub и сервера монтируют каталог только для чтения. Проверку TLS не отключать.

Пользователь открывает бота → `/start` → «Открыть приложение» → входит в аккаунт проекта. Вход в MAX не заменяет регистрацию в проекте. Команда `/guide` объясняет основные функции, `/status` проверяет связь, `/stop` отключает уведомления.

### Напоминания и заявки капитану

В профиле нужно подключить MAX и подтвердить связь со своим аккаунтом. После этого бот доставляет напоминания о событиях и новые заявки в команду. Капитан получает имя заявителя, описание навыков и кнопку открытия события. В событии: «Команды и отзывы» → своя команда → принять/отклонить.

Фоновый обработчик проверяет очередь примерно каждые 30 секунд. Повторная подача уже существующей заявки не создаёт новую отправку. Отозванные/рассмотренные заявки, завершившиеся события и отключённые подключения не доставляются. После сетевой ошибки выполняется отложенный повтор; при запрете со стороны MAX подключение выключается. Старые заявки, созданные до обновления, автоматически не рассылаются. При аварии между отправкой и фиксацией результата теоретически возможен повтор сообщения.

Без подключения MAX заявка всё равно сохраняется и видна капитану в команде. Это сообщение внутри MAX, не SMS на телефон.

## 7. Обновление и резервная копия

Перед обновлением сохрани БД и загрузки. Пример для CloudPub (файлы создаются внутри контейнеров, чтобы избежать повреждения бинарного дампа перенаправлением PowerShell):

```powershell
docker compose --env-file .env.cloudpub -f compose.cloudpub.yaml exec -T db pg_dump -U budvkurse -d budvkurse_app -Fc -f /tmp/budvkurse.dump
docker compose --env-file .env.cloudpub -f compose.cloudpub.yaml cp db:/tmp/budvkurse.dump ./budvkurse.dump
docker compose --env-file .env.cloudpub -f compose.cloudpub.yaml exec -T app tar -czf /tmp/uploads.tar.gz -C /app/beckend uploads
docker compose --env-file .env.cloudpub -f compose.cloudpub.yaml cp app:/tmp/uploads.tar.gz ./uploads.tar.gz
git pull --ff-only
docker compose --env-file .env.cloudpub -f compose.cloudpub.yaml up -d --build --wait
```

Сохраняй резервные копии вне публичного каталога и Git. Добавление новых полей уведомлений выполняет миграция `0008`. Не выполняй `down -v`: эта команда удаляет тома с данными. Обычный перезапуск — `restart`, остановка — `stop`; после остановки для запуска используй `up -d`.

Для восстановления в отдельном проверочном развёртывании: скопируй дамп командой `docker compose ... cp ./budvkurse.dump db:/tmp/budvkurse.dump`, затем выполни `docker compose ... exec -T db pg_restore -U budvkurse -d budvkurse_app --clean --if-exists --no-owner /tmp/budvkurse.dump`. **Это заменяет данные целевой базы**. Восстанавливай только в предназначенную для этого базу. Загрузки восстанови из архива в том `/app/beckend/uploads` с владельцем `app`. Для каждой конфигурации используй её собственные `--env-file` и `-f` вместо многоточия.

## 8. Диагностика и тесты

```powershell
docker compose --env-file .env.cloudpub -f compose.cloudpub.yaml ps
docker compose --env-file .env.cloudpub -f compose.cloudpub.yaml logs --tail 100 app
docker compose --env-file .env.cloudpub -f compose.cloudpub.yaml exec app python -m alembic current
```

При недоступности сайта сначала проверь `/health`, контейнеры и сеть. При ошибке MAX проверь токен, доверенные CA, webhook и URL мини-приложения. Если нет событий — сбрось фильтры и проверь статус публикации. Если уведомлений нет — подключение MAX, `/status`, `/stop`, время события и логи worker. Старые сообщения бота сохраняют прежние кнопки: отправь `/start` заново.

Автотесты запускаются из исходников, в рабочем Docker-образе тестовые файлы исключены. Для локального тестирования:

```powershell
cd beckend
py -3.13 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-lock.txt
.\.venv\Scripts\python.exe -m pytest -q
cd ..
node --test frontend/tests/*.test.cjs
```

По умолчанию тесты используют временную SQLite. Для PostgreSQL задай `TEST_DATABASE_URL` на **отдельную** тестовую БД с именем, заканчивающимся `_test`: тесты очищают её. Никогда не направляй тесты в рабочую БД. Миграции с нуля и `alembic check` также проверяй на отдельной БД. Реальные токены MAX не нужны для тестов доставки: отправка подменяется тестовым обработчиком.

## 9. Секреты, файлы и лицензии

Не загружай в Git `.env*` с секретами, `.runtime`, `.admin-access.txt`, загрузки, дампы и виртуальные окружения. Шаблон `.env.example` допустим. Перед отправкой проверяй `git status` и `git diff --cached`. GitHub хранит исходники, а не работающие контейнеры и БД.

Сторонние библиотеки и лицензии сохранены в `vendor`; их комментарии и уведомления об авторских правах не удаляются. Ниже сохранены сведения об источниках изображений.
