# Справочник: таблицы, схемы, CRUD и ручки

Составлен по готовому коду. Общий порядок работы и запуск — в README.md.

## 1. Таблицы

`NULL` — можно не указывать. `FK` — ссылка на другую таблицу. Все id — INTEGER. У связок есть собственный id и UNIQUE на пару ссылок.

### cities

| Поле | PostgreSQL | NULL | Связь / значение по умолчанию |
|---|---|---|---|
| id | INTEGER | нет | PRIMARY KEY |
| name | VARCHAR(120) | нет | — |
| region | VARCHAR(120) | нет | — |
| country_code | VARCHAR(2) | нет | — |
| latitude | FLOAT | нет | — |
| longitude | FLOAT | нет | — |
| created_at | TIMESTAMP WITH TIME ZONE | нет | DEFAULT now() |
| updated_at | TIMESTAMP WITH TIME ZONE | нет | DEFAULT now() |

Проверка: `latitude BETWEEN -90 AND 90`.

Проверка: `longitude BETWEEN -180 AND 180`.

Проверка: `length(country_code) = 2`.

### topics

| Поле | PostgreSQL | NULL | Связь / значение по умолчанию |
|---|---|---|---|
| id | INTEGER | нет | PRIMARY KEY |
| name | VARCHAR(100) | нет | — |
| slug | VARCHAR(100) | нет | — |
| created_at | TIMESTAMP WITH TIME ZONE | нет | DEFAULT now() |
| updated_at | TIMESTAMP WITH TIME ZONE | нет | DEFAULT now() |

Уникально: `slug`.

### schools

| Поле | PostgreSQL | NULL | Связь / значение по умолчанию |
|---|---|---|---|
| id | INTEGER | нет | PRIMARY KEY |
| city_id | INTEGER | нет | FK cities.id; ON DELETE RESTRICT |
| name | VARCHAR(200) | нет | — |
| address | TEXT | нет | — |
| latitude | DOUBLE PRECISION | да | — |
| longitude | DOUBLE PRECISION | да | — |
| is_active | BOOLEAN | нет | DEFAULT true |
| created_at | TIMESTAMP WITH TIME ZONE | нет | DEFAULT now() |
| updated_at | TIMESTAMP WITH TIME ZONE | нет | DEFAULT now() |

Проверка: `latitude BETWEEN -90 AND 90`.

Проверка: `longitude BETWEEN -180 AND 180`.

Проверка: `(latitude IS NULL AND longitude IS NULL) OR (latitude IS NOT NULL AND longitude IS NOT NULL)`.

### users

| Поле | PostgreSQL | NULL | Связь / значение по умолчанию |
|---|---|---|---|
| id | INTEGER | нет | PRIMARY KEY |
| email | VARCHAR(254) | нет | — |
| password_hash | VARCHAR | нет | — |
| name | VARCHAR(80) | нет | — |
| role | VARCHAR(20) | нет | DEFAULT student |
| grade | INTEGER | да | — |
| city_id | INTEGER | да | FK cities.id; ON DELETE SET NULL |
| school_id | INTEGER | да | FK schools.id; ON DELETE SET NULL |
| is_active | BOOLEAN | нет | DEFAULT true |
| created_at | TIMESTAMP WITH TIME ZONE | нет | DEFAULT now() |
| updated_at | TIMESTAMP WITH TIME ZONE | нет | DEFAULT now() |

Проверка: `grade BETWEEN 1 AND 11`.

Проверка: `role IN ('student', 'organizer', 'admin')`.

Уникально: `email`.

### files

| Поле | PostgreSQL | NULL | Связь / значение по умолчанию |
|---|---|---|---|
| id | INTEGER | нет | PRIMARY KEY |
| uploaded_by | INTEGER | нет | FK users.id; ON DELETE RESTRICT |
| storage_key | VARCHAR(100) | нет | — |
| original_name | VARCHAR(255) | нет | — |
| mime_type | VARCHAR(100) | нет | — |
| size_bytes | BIGINT | нет | — |
| created_at | TIMESTAMP WITH TIME ZONE | нет | DEFAULT now() |

Уникально: `storage_key`.

### sessions

| Поле | PostgreSQL | NULL | Связь / значение по умолчанию |
|---|---|---|---|
| id | INTEGER | нет | PRIMARY KEY |
| user_id | INTEGER | нет | FK users.id; ON DELETE CASCADE |
| refresh_token_hash | VARCHAR | нет | — |
| created_at | TIMESTAMP WITH TIME ZONE | нет | DEFAULT now() |
| expires_at | TIMESTAMP WITH TIME ZONE | нет | — |
| revoked_at | TIMESTAMP WITH TIME ZONE | да | — |

Уникально: `refresh_token_hash`.

### user_interests

| Поле | PostgreSQL | NULL | Связь / значение по умолчанию |
|---|---|---|---|
| id | INTEGER | нет | PRIMARY KEY |
| user_id | INTEGER | нет | FK users.id; ON DELETE CASCADE |
| topic_id | INTEGER | нет | FK topics.id; ON DELETE CASCADE |

Уникально: `user_id, topic_id`.

### events

| Поле | PostgreSQL | NULL | Связь / значение по умолчанию |
|---|---|---|---|
| id | INTEGER | нет | PRIMARY KEY |
| organizer_id | INTEGER | нет | FK users.id; ON DELETE RESTRICT |
| title | VARCHAR(150) | нет | — |
| description | TEXT | нет | — |
| category | VARCHAR(20) | нет | — |
| status | VARCHAR(20) | нет | DEFAULT draft |
| city_id | INTEGER | нет | FK cities.id; ON DELETE RESTRICT |
| school_id | INTEGER | да | FK schools.id; ON DELETE SET NULL |
| cover_file_id | INTEGER | да | FK files.id; ON DELETE SET NULL |
| starts_at | TIMESTAMP WITH TIME ZONE | нет | — |
| ends_at | TIMESTAMP WITH TIME ZONE | нет | — |
| timezone | VARCHAR(64) | нет | DEFAULT Europe/Moscow |
| registration_deadline | TIMESTAMP WITH TIME ZONE | да | — |
| format | VARCHAR(10) | нет | — |
| place_name | VARCHAR(200) | да | — |
| address | TEXT | да | — |
| latitude | DOUBLE PRECISION | да | — |
| longitude | DOUBLE PRECISION | да | — |
| online_url | TEXT | да | — |
| min_grade | INTEGER | да | — |
| max_grade | INTEGER | да | — |
| min_age | INTEGER | да | — |
| max_age | INTEGER | да | — |
| price | NUMERIC(10, 2) | нет | DEFAULT 0 |
| capacity | INTEGER | да | — |
| registration_mode | VARCHAR(10) | нет | DEFAULT none |
| registration_url | TEXT | да | — |
| take_with_you | TEXT | да | — |
| created_at | TIMESTAMP WITH TIME ZONE | нет | DEFAULT now() |
| updated_at | TIMESTAMP WITH TIME ZONE | нет | DEFAULT now() |

Проверка: `category IN ('city', 'school', 'olympiad', 'project')`.

Проверка: `status IN ('draft', 'pending', 'published', 'rejected', 'cancelled')`.

Проверка: `format IN ('offline', 'online')`.

Проверка: `registration_mode IN ('internal', 'external', 'none')`.

Проверка: `ends_at > starts_at`.

Проверка: `registration_deadline <= starts_at`.

Проверка: `latitude BETWEEN -90 AND 90`.

Проверка: `longitude BETWEEN -180 AND 180`.

Проверка: `(latitude IS NULL AND longitude IS NULL) OR (latitude IS NOT NULL AND longitude IS NOT NULL)`.

Проверка: `min_grade BETWEEN 1 AND 11`.

Проверка: `max_grade BETWEEN 1 AND 11`.

Проверка: `min_grade <= max_grade`.

Проверка: `min_age >= 0`.

Проверка: `max_age >= 0`.

Проверка: `min_age <= max_age`.

Проверка: `price >= 0`.

Проверка: `capacity > 0`.

### event_moderation

| Поле | PostgreSQL | NULL | Связь / значение по умолчанию |
|---|---|---|---|
| id | INTEGER | нет | PRIMARY KEY |
| event_id | INTEGER | нет | FK events.id; ON DELETE RESTRICT |
| reviewer_id | INTEGER | нет | FK users.id; ON DELETE RESTRICT |
| decision | VARCHAR(20) | нет | — |
| comment | TEXT | да | — |
| created_at | TIMESTAMP WITH TIME ZONE | нет | DEFAULT now() |

Проверка: `decision IN ('approved', 'rejected')`.

### event_topics

| Поле | PostgreSQL | NULL | Связь / значение по умолчанию |
|---|---|---|---|
| id | INTEGER | нет | PRIMARY KEY |
| event_id | INTEGER | нет | FK events.id; ON DELETE CASCADE |
| topic_id | INTEGER | нет | FK topics.id; ON DELETE RESTRICT |

Уникально: `event_id, topic_id`.

### favorites

| Поле | PostgreSQL | NULL | Связь / значение по умолчанию |
|---|---|---|---|
| id | INTEGER | нет | PRIMARY KEY |
| user_id | INTEGER | нет | FK users.id; ON DELETE CASCADE |
| event_id | INTEGER | нет | FK events.id; ON DELETE CASCADE |
| created_at | TIMESTAMP WITH TIME ZONE | нет | DEFAULT now() |

Уникально: `user_id, event_id`.

### plans

| Поле | PostgreSQL | NULL | Связь / значение по умолчанию |
|---|---|---|---|
| id | INTEGER | нет | PRIMARY KEY |
| user_id | INTEGER | нет | FK users.id; ON DELETE CASCADE |
| event_id | INTEGER | нет | FK events.id; ON DELETE CASCADE |
| reminder_minutes_before | INTEGER | да | — |
| created_at | TIMESTAMP WITH TIME ZONE | нет | DEFAULT now() |
| updated_at | TIMESTAMP WITH TIME ZONE | нет | DEFAULT now() |

Проверка: `reminder_minutes_before BETWEEN 0 AND 10080`.

Уникально: `user_id, event_id`.

### registrations

| Поле | PostgreSQL | NULL | Связь / значение по умолчанию |
|---|---|---|---|
| id | INTEGER | нет | PRIMARY KEY |
| user_id | INTEGER | нет | FK users.id; ON DELETE RESTRICT |
| event_id | INTEGER | нет | FK events.id; ON DELETE RESTRICT |
| status | VARCHAR(20) | нет | DEFAULT registered |
| registered_at | TIMESTAMP WITH TIME ZONE | нет | DEFAULT now() |
| cancelled_at | TIMESTAMP WITH TIME ZONE | да | — |

Проверка: `status IN ('registered', 'cancelled')`.

Уникально: `user_id, event_id`.

## 2. Pydantic-схемы

Create принимает создание. Update принимает частичное изменение. Read — ответ клиенту. Пропущенное поле PATCH не меняется; null допустим только там, где это явно разрешено. Подробнее о каждом поле — в docs/openapi.json и Swagger /docs.

| Файл | Схемы и поля (включая унаследованные) |
|---|---|
| schemas/auth.py | **RegisterRequest**: email, password, name, role (student или organizer; по умолчанию student)<br>**LoginRequest**: email, password<br>**RefreshRequest**: refresh_token<br>**TokenPair**: access_token, refresh_token, token_type |
| schemas/cities.py | **CityCreate**: name, region, country_code, latitude, longitude<br>**CityUpdate**: name, region, country_code, latitude, longitude<br>**CityRead**: created_at, updated_at, name, region, country_code, latitude, longitude, id |
| schemas/common.py | **InputModel**: общая конфигурация<br>**ReadModel**: общая конфигурация<br>**PatchModel**: общая конфигурация<br>**Pagination**: page, limit<br>**Page**: items, total, page, limit<br>**Timestamps**: created_at, updated_at |
| schemas/events.py | **EventCreate**: title, description, category, city_id, school_id, cover_file_id, topic_ids, starts_at, ends_at, timezone, registration_deadline, format, place_name, address, latitude, longitude, online_url, min_grade, max_grade, min_age, max_age, price, capacity, registration_mode, registration_url, take_with_you<br>**EventUpdate**: title, description, category, city_id, school_id, cover_file_id, topic_ids, starts_at, ends_at, timezone, registration_deadline, format, place_name, address, latitude, longitude, online_url, min_grade, max_grade, min_age, max_age, price, capacity, registration_mode, registration_url, take_with_you<br>**EventRead**: created_at, updated_at, title, description, category, city_id, school_id, cover_file_id, topic_ids, starts_at, ends_at, timezone, registration_deadline, format, place_name, address, latitude, longitude, online_url, min_grade, max_grade, min_age, max_age, price, capacity, registration_mode, registration_url, take_with_you, id, organizer_id, status, cover_url, is_favorite, in_plans<br>**EventShort**: id, title, category, status, city_id, school_id, starts_at, ends_at, format, price, cover_url, is_favorite, in_plans<br>**EventFilters**: search, city_id, school_id, category, topic_id, date_from, date_to, grade, age, format, price_min, price_max, place, sort, page, limit<br>**MapFilters**: search, city_id, school_id, category, topic_id, date_from, date_to, grade, age, format, price_min, price_max, place, sort, page, limit, west, south, east, north<br>**MapEventRead**: id, title, latitude, longitude, starts_at, school_id |
| schemas/favorites.py | **FavoriteRead**: event, created_at |
| schemas/files.py | **FileRead**: id, url, mime_type, size_bytes |
| schemas/moderation.py | **RejectEventRequest**: comment<br>**ModerationRead**: id, event_id, reviewer_id, decision, comment, created_at |
| schemas/plans.py | **PlanWrite**: reminder_minutes_before<br>**PlanRead**: event, reminder_minutes_before, created_at<br>**PlanFilters**: page, limit, date_from, date_to |
| schemas/registrations.py | **RegistrationRead**: id, user_id, event_id, status, registered_at, cancelled_at |
| schemas/schools.py | **SchoolCreate**: city_id, name, address, latitude, longitude<br>**SchoolUpdate**: city_id, name, address, latitude, longitude, is_active<br>**SchoolRead**: created_at, updated_at, city_id, name, address, latitude, longitude, id, is_active |
| schemas/topics.py | **TopicCreate**: name, slug<br>**TopicUpdate**: name, slug<br>**TopicRead**: created_at, updated_at, name, slug, id |
| schemas/users.py | **UserUpdate**: name, grade, city_id, school_id<br>**UserRead**: created_at, updated_at, id, email, name, role, grade, city_id, school_id, is_active<br>**InterestsUpdate**: topic_ids |

## 3. CRUD

CRUD выполняет запросы к БД. Аргумент db — AsyncSession. Возвращает ORM-записи; page/list со страницами возвращают (список, общее количество). Проверки прав и бизнес-правила находятся в services.

| Файл | Назначение | Функции |
|---|---|---|
| crud/cities.py | Города: чтение и изменение справочника. | `create_city(db, data)`<br>`get_city(db, row_id, *, lock=False)`<br>`update_city(db, row, changes)`<br>`delete_city(db, row)`<br>`list_cities(db)` |
| crud/common.py | Общие операции SQLAlchemy: добавить, получить, изменить, удалить, получить страницу. | `create(db, model, values)`<br>`get(db, model, row_id, *, lock=False)`<br>`update(db, row, changes)`<br>`remove(db, row)`<br>`page(db, stmt, pagination)` |
| crud/events.py | Мероприятия: запросы, фильтры ленты и карты, сохранение изменений. | `get_event(db, event_id, *, lock=False)`<br>`create_event(db, organizer_id, values)`<br>`filtered_query(filters, user=None)`<br>`list_events(db, filters, user=None)`<br>`list_map_events(db, filters, user=None)`<br>`update_event(db, event, changes)`<br>`set_event_status(db, event, status)`<br>`delete_event(db, event)` |
| crud/favorites.py | Избранное пользователя: добавление, список и удаление. | `get_favorite(db, user_id, event_id)`<br>`add_favorite(db, user_id, event_id)`<br>`list_favorites(db, user_id, pagination)`<br>`remove_favorite(db, favorite)` |
| crud/files.py | Метаданные файлов в БД. Само изображение хранится в uploads. | `create_file(db, data)`<br>`get_file(db, row_id, *, lock=False)`<br>`update_file(db, row, changes)`<br>`delete_file(db, row)` |
| crud/interests.py | Связи: интересы пользователя и темы мероприятия. Замена списка целиком. | `get_user_interests(db, user_id)`<br>`replace_user_interests(db, user_id, topic_ids)`<br>`replace_event_topics(db, event_id, topic_ids)`<br>`event_topic_ids(db, event_id)` |
| crud/moderation.py | История модерации: решения администратора по мероприятиям. | `create_review(db, event_id, reviewer_id, decision, comment=None)`<br>`list_reviews(db, event_id)` |
| crud/plans.py | Личные планы: сохранение, календарь за период и удаление. | `get_plan(db, user_id, event_id)`<br>`upsert_plan(db, user_id, event_id, data)`<br>`list_plans(db, user_id, filters)`<br>`remove_plan(db, plan)` |
| crud/registrations.py | Участники: запись, отмена, подсчёт занятых мест и списки. | `get_registration(db, user_id, event_id)`<br>`count_registered(db, event_id)`<br>`create_registration(db, user_id, event_id)`<br>`cancel_registration(db, row)`<br>`list_event_registrations(db, event_id, pagination)`<br>`list_user_registrations(db, user_id, pagination)` |
| crud/schools.py | Школы: поиск по городу и управление справочником. | `create_school(db, data)`<br>`get_school(db, row_id, *, lock=False)`<br>`update_school(db, row, changes)`<br>`delete_school(db, row)`<br>`list_schools(db, city_id, pagination)` |
| crud/sessions.py | Сессии: хеши refresh-токенов, сроки действия и отзыв. | `create_session(db, user_id, token_hash, expires_at)`<br>`get_session_by_hash(db, token_hash, *, lock=False)`<br>`revoke_session(db, session)`<br>`revoke_user_sessions(db, user_id)` |
| crud/topics.py | Темы мероприятий: чтение и изменение справочника. | `create_topic(db, data)`<br>`get_topic(db, row_id, *, lock=False)`<br>`update_topic(db, row, changes)`<br>`delete_topic(db, row)`<br>`list_topics(db)` |
| crud/users.py | Пользователи: создание, поиск, изменение профиля и деактивация. | `get_user(db, user_id, *, lock=False)`<br>`get_user_by_email(db, email)`<br>`create_user(db, data, password_hash)`<br>`update_user(db, user, changes)`<br>`deactivate_user(db, user)` |

## 4. Сервисы

| Файл | За что отвечает |
|---|---|
| services/auth.py | Хеш пароля, вход, ротация токенов, выход |
| services/users.py | Профиль, соответствие школы городу, интересы и деактивация |
| services/events.py | Доступ к событию, ссылки, создание/редактирование, статусы, сбор карточек |
| services/catalog.py | Правила изменения и удаления городов, школ и тем |
| services/personal.py | Избранное, планы и запись участника с блокировкой места |
| services/files.py | Проверка изображения, сохранение, доступ и удаление файла |
| services/common.py | Проверка существования записей, связей и схем |

## 5. Все HTTP-ручки

Авторизованный — любой активный аккаунт. Организатор — organizer/admin. Для изменения чужих объектов дополнительно проверяется владелец. GET опубликованных карточек доступен всем вошедшим пользователям. Все маршруты данных теперь дополнительно защищены get_current_user при подключении роутеров в main.py. Если передать недействительный токен даже на публичную ручку, ответ будет 401.

| Метод | Путь | Что делает | Доступ |
|---|---|---|---|
| GET | `/health` | Проверить доступность API и базы | Все / по доступности объекта |
| POST | `/api/v1/auth/register` | Создать аккаунт ученика или организатора | Все / по доступности объекта |
| POST | `/api/v1/auth/login` | Войти по email и паролю | Все / по доступности объекта |
| POST | `/api/v1/auth/refresh` | Обновить токены; старые перестанут работать | Все / по доступности объекта |
| POST | `/api/v1/auth/logout` | Отозвать сессию | Все / по доступности объекта |
| GET | `/api/v1/cities` | Список городов | Авторизованный, по доступности объекта |
| GET | `/api/v1/cities/{city_id}` | Город по id | Авторизованный, по доступности объекта |
| POST | `/api/v1/cities` | Добавить город | Админ |
| PATCH | `/api/v1/cities/{city_id}` | Изменить город | Админ |
| DELETE | `/api/v1/cities/{city_id}` | Удалить город без связанных данных | Админ |
| GET | `/api/v1/schools` | Активные школы, фильтр по городу | Авторизованный, по доступности объекта |
| GET | `/api/v1/schools/{school_id}` | Школа по id | Авторизованный, по доступности объекта |
| POST | `/api/v1/schools` | Добавить школу | Админ |
| PATCH | `/api/v1/schools/{school_id}` | Изменить школу | Админ |
| DELETE | `/api/v1/schools/{school_id}` | Деактивировать школу | Админ |
| GET | `/api/v1/topics` | Список тем | Авторизованный, по доступности объекта |
| GET | `/api/v1/topics/{topic_id}` | Тема по id | Авторизованный, по доступности объекта |
| POST | `/api/v1/topics` | Добавить тему | Админ |
| PATCH | `/api/v1/topics/{topic_id}` | Изменить тему | Админ |
| DELETE | `/api/v1/topics/{topic_id}` | Удалить неиспользуемую тему | Админ |
| GET | `/api/v1/events` | Лента и календарь: поиск, фильтры, сортировка | Авторизованный, по доступности объекта |
| GET | `/api/v1/events/map` | Метки в видимой области карты | Авторизованный, по доступности объекта |
| GET | `/api/v1/me/events` | Мои мероприятия, включая черновики | Организатор/админ, проверка владельца |
| GET | `/api/v1/admin/events` | Все мероприятия, необязательный фильтр по статусу | Админ |
| GET | `/api/v1/events/{event_id}` | Полная карточка мероприятия | Авторизованный, по доступности объекта |
| POST | `/api/v1/events` | Создать черновик | Организатор/админ, проверка владельца |
| PATCH | `/api/v1/events/{event_id}` | Изменить мероприятие; опубликованное обновляется сразу | Организатор/админ, проверка владельца |
| DELETE | `/api/v1/events/{event_id}` | Удалить событие вместе со связанными записями | Админ — любое; организатор — свой черновик |
| POST | `/api/v1/events/{event_id}/submit` | Отправить на модерацию | Организатор/админ, проверка владельца |
| POST | `/api/v1/events/{event_id}/publish` | Опубликовать без предварительного одобрения | Организатор — своё; админ — любое |
| POST | `/api/v1/events/{event_id}/reject` | Отклонить с комментарием | Админ |
| POST | `/api/v1/events/{event_id}/cancel` | Отменить мероприятие | Организатор/админ, проверка владельца |
| GET | `/api/v1/events/{event_id}/moderation` | История решений модератора | Организатор/админ, проверка владельца |
| POST | `/api/v1/files` | Загрузить фотографию | Организатор/админ, проверка владельца |
| GET | `/api/v1/files/{file_id}/content` | Изображение; чужие неопубликованные обложки скрыты | Авторизованный, по доступности объекта |
| DELETE | `/api/v1/files/{file_id}` | Удалить неиспользуемую фотографию | Организатор/админ, проверка владельца |
| GET | `/api/v1/me/favorites` | Моё избранное | Авторизованный |
| PUT | `/api/v1/me/favorites/{event_id}` | Добавить в избранное без дубликатов | Авторизованный |
| DELETE | `/api/v1/me/favorites/{event_id}` | Убрать из избранного | Авторизованный |
| GET | `/api/v1/me/plans` | Личный календарь за период | Авторизованный |
| PUT | `/api/v1/me/plans/{event_id}` | Добавить в планы или изменить напоминание | Авторизованный |
| DELETE | `/api/v1/me/plans/{event_id}` | Убрать из планов | Авторизованный |
| POST | `/api/v1/events/{event_id}/registrations` | Записаться участником | Авторизованный |
| DELETE | `/api/v1/events/{event_id}/registrations/me` | Отменить свою запись | Авторизованный |
| GET | `/api/v1/me/registrations` | Мои записи на мероприятия | Авторизованный |
| GET | `/api/v1/events/{event_id}/registrations` | Список участников своего мероприятия | Организатор/админ, проверка владельца |
| GET | `/api/v1/me` | Мой профиль | Авторизованный |
| PATCH | `/api/v1/me` | Изменить профиль, сохранив пропущенные поля | Авторизованный |
| DELETE | `/api/v1/me` | Деактивировать аккаунт и отозвать сессии | Авторизованный |
| GET | `/api/v1/me/interests` | Мои интересы | Авторизованный |
| PUT | `/api/v1/me/interests` | Заменить список интересов | Авторизованный |

После интеграции EventShort/MapEventRead также возвращают площадку, координаты, часовой пояс, условия участия и topic_ids. RegistrationRead содержит event для личного списка, participant_name и grade для списка участников. Точные текущие поля — в openapi.json.
