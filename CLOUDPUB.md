# Запуск через Docker и CloudPub

Адрес сайта: https://kindly-competent-polecat.cloudpub.ru/. Все мероприятия, аккаунты и напоминания используют одну базу. Компьютер должен быть включён, подключён к интернету и не находиться в спящем режиме.

Открой Docker Desktop и запусти `start-docker.cmd` в корне проекта. В терминале из этой папки:

```powershell
docker compose --env-file .env.cloudpub -f compose.cloudpub.yaml up -d --build --wait
docker compose --env-file .env.cloudpub -f compose.cloudpub.yaml ps
```

В локальном файле `.env.cloudpub` находятся PUBLIC_BASE_URL, CLOUDPUB_TOKEN, POSTGRES_PASSWORD, JWT_SECRET и настройки MAX. Ключи исключены из Git. Не удаляй тома database, uploads и cloudpub-config: в них находятся данные и настройки постоянного адреса.

Проверка: https://kindly-competent-polecat.cloudpub.ru/health должна вернуть статус ok. Для подключения webhook и меню на новом развёртывании выполни:

```powershell
docker compose --env-file .env.cloudpub -f compose.cloudpub.yaml exec app python -m scripts.setup_max --register
```

URL для настроек мини-приложения у организатора MAX: https://kindly-competent-polecat.cloudpub.ru/?max=1.

Организаторы подтвердили подключение этого адреса 5 ноября 2026. Бот открывает только мини-приложение. Инструкция пользователей: [HOW-TO-OPEN.md](HOW-TO-OPEN.md).
