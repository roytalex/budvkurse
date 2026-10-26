# Запуск через Go Live в VS Code

1. Открой в VS Code папку **budvkurse целиком**, где находятся `frontend`, `beckend`, `assets`, `vendor` и `.vscode`.
2. В терминале VS Code запусти бэкенд:

   ```powershell
   cd C:\Users\roytb\Desktop\budvkurse\beckend
   .\.venv\Scripts\python.exe -m uvicorn main:app --reload --host 127.0.0.1 --port 4174
   ```

   Если он уже работает на 4174, второй раз запускать не нужно. PostgreSQL тоже должен работать.

3. Открой `frontend/index.html` и нажми **Go Live**. Если Live Server уже был запущен, останови и запусти его снова, чтобы он прочитал настройки.
4. Открой нужный адрес: **http://127.0.0.1:5500/frontend/index.html**. Go Live также может автоматически открыть `/index.html` — оба адреса показывают тот же сайт. На новом адресе нужно войти в тот же аккаунт заново: данные пользователей и событий остаются в прежней БД.

## Где изменить адрес

Настройки лежат в `.vscode/settings.json`:

- `liveServer.settings.host` — адрес, на котором запускается сайт; сейчас `127.0.0.1`.
- `liveServer.settings.port` — порт сайта; сейчас `5500`.
- `liveServer.settings.proxy.proxyUri` — адрес бэкенда с `/api` в конце; сейчас `http://127.0.0.1:4174/api`.

Для другого порта сайта достаточно поменять `liveServer.settings.port` и перезапустить Go Live. Если поменял порт Uvicorn, укажи тот же порт в `proxyUri`. Порты сайта и бэкенда должны различаться.

Go Live раздаёт фронтенд и пересылает запросы `/api/...` в FastAPI, включая вход, обновление токенов и фотографии. Поэтому адрес сервера не нужно прописывать в каждом JS-файле и не требуется расширять CORS. Это штатная [настройка proxy расширения Live Server](https://github.com/ritwickdey/vscode-live-server/blob/master/docs/settings.md).

Корень Live Server — только `frontend`; пути `/frontend`, `/assets` и `/vendor` подключены отдельно. Каталог `beckend`, `.env` и файл с локальными данными входа не раздаются сайтом. Не меняй `root` на `/`.

Go Live сам не запускает Python и PostgreSQL. Терминал с Uvicorn оставь работающим. Если видишь ошибку соединения или `ECONNREFUSED`, проверь бэкенд и `proxyUri`.
