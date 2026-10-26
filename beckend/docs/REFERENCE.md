# Таблицы, схемы и API

Актуальный справочник по коду. Бизнес-правила достижений: [ACHIEVEMENTS.md](../../ACHIEVEMENTS.md).

## Таблицы

Таблицы conversations/messages и старые поля reminder_* сохранены только для совместимости прежних миграций и сохранности истории. Доступа к чатам и напоминаниям через API больше нет.

### cities

| Поле | Тип PostgreSQL | NULL | Связь |
|---|---|---|---|
| id | INTEGER | нет | — |
| name | VARCHAR(120) | нет | — |
| region | VARCHAR(120) | нет | — |
| country_code | VARCHAR(2) | нет | — |
| latitude | FLOAT | нет | — |
| longitude | FLOAT | нет | — |
| created_at | TIMESTAMP WITH TIME ZONE | нет | — |
| updated_at | TIMESTAMP WITH TIME ZONE | нет | — |

### topics

| Поле | Тип PostgreSQL | NULL | Связь |
|---|---|---|---|
| id | INTEGER | нет | — |
| name | VARCHAR(100) | нет | — |
| slug | VARCHAR(100) | нет | — |
| created_at | TIMESTAMP WITH TIME ZONE | нет | — |
| updated_at | TIMESTAMP WITH TIME ZONE | нет | — |

### schools

| Поле | Тип PostgreSQL | NULL | Связь |
|---|---|---|---|
| id | INTEGER | нет | — |
| city_id | INTEGER | нет | cities.id (RESTRICT) |
| name | VARCHAR(200) | нет | — |
| address | TEXT | нет | — |
| latitude | DOUBLE PRECISION | да | — |
| longitude | DOUBLE PRECISION | да | — |
| is_active | BOOLEAN | нет | — |
| created_at | TIMESTAMP WITH TIME ZONE | нет | — |
| updated_at | TIMESTAMP WITH TIME ZONE | нет | — |

### users

| Поле | Тип PostgreSQL | NULL | Связь |
|---|---|---|---|
| id | INTEGER | нет | — |
| email | VARCHAR(254) | нет | — |
| password_hash | VARCHAR | нет | — |
| name | VARCHAR(80) | нет | — |
| role | VARCHAR(20) | нет | — |
| grade | INTEGER | да | — |
| city_id | INTEGER | да | cities.id (SET NULL) |
| school_id | INTEGER | да | schools.id (SET NULL) |
| is_active | BOOLEAN | нет | — |
| created_at | TIMESTAMP WITH TIME ZONE | нет | — |
| updated_at | TIMESTAMP WITH TIME ZONE | нет | — |

### files

| Поле | Тип PostgreSQL | NULL | Связь |
|---|---|---|---|
| id | INTEGER | нет | — |
| uploaded_by | INTEGER | нет | users.id (RESTRICT) |
| storage_key | VARCHAR(100) | нет | — |
| original_name | VARCHAR(255) | нет | — |
| mime_type | VARCHAR(100) | нет | — |
| size_bytes | BIGINT | нет | — |
| created_at | TIMESTAMP WITH TIME ZONE | нет | — |

### sessions

| Поле | Тип PostgreSQL | NULL | Связь |
|---|---|---|---|
| id | INTEGER | нет | — |
| user_id | INTEGER | нет | users.id (CASCADE) |
| refresh_token_hash | VARCHAR | нет | — |
| created_at | TIMESTAMP WITH TIME ZONE | нет | — |
| expires_at | TIMESTAMP WITH TIME ZONE | нет | — |
| revoked_at | TIMESTAMP WITH TIME ZONE | да | — |

### user_interests

| Поле | Тип PostgreSQL | NULL | Связь |
|---|---|---|---|
| id | INTEGER | нет | — |
| user_id | INTEGER | нет | users.id (CASCADE) |
| topic_id | INTEGER | нет | topics.id (CASCADE) |

### events

| Поле | Тип PostgreSQL | NULL | Связь |
|---|---|---|---|
| id | INTEGER | нет | — |
| organizer_id | INTEGER | нет | users.id (RESTRICT) |
| title | VARCHAR(150) | нет | — |
| description | TEXT | нет | — |
| category | VARCHAR(20) | нет | — |
| status | VARCHAR(20) | нет | — |
| city_id | INTEGER | нет | cities.id (RESTRICT) |
| school_id | INTEGER | да | schools.id (SET NULL) |
| cover_file_id | INTEGER | да | files.id (SET NULL) |
| starts_at | TIMESTAMP WITH TIME ZONE | нет | — |
| ends_at | TIMESTAMP WITH TIME ZONE | нет | — |
| timezone | VARCHAR(64) | нет | — |
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
| price | NUMERIC(10, 2) | нет | — |
| capacity | INTEGER | да | — |
| registration_mode | VARCHAR(10) | нет | — |
| registration_url | TEXT | да | — |
| take_with_you | TEXT | да | — |
| created_at | TIMESTAMP WITH TIME ZONE | нет | — |
| updated_at | TIMESTAMP WITH TIME ZONE | нет | — |

### attendance

| Поле | Тип PostgreSQL | NULL | Связь |
|---|---|---|---|
| id | INTEGER | нет | — |
| user_id | INTEGER | нет | users.id (CASCADE) |
| event_id | INTEGER | нет | events.id (CASCADE) |
| confirmed_by | INTEGER | да | users.id (SET NULL) |
| confirmed_at | TIMESTAMP WITH TIME ZONE | нет | — |

### conversations

| Поле | Тип PostgreSQL | NULL | Связь |
|---|---|---|---|
| id | INTEGER | нет | — |
| event_id | INTEGER | да | events.id (SET NULL) |
| event_title | VARCHAR(150) | нет | — |
| participant_id | INTEGER | нет | users.id (CASCADE) |
| organizer_id | INTEGER | нет | users.id (CASCADE) |
| participant_read_id | INTEGER | нет | — |
| organizer_read_id | INTEGER | нет | — |
| created_at | TIMESTAMP WITH TIME ZONE | нет | — |
| updated_at | TIMESTAMP WITH TIME ZONE | нет | — |

### event_moderation

| Поле | Тип PostgreSQL | NULL | Связь |
|---|---|---|---|
| id | INTEGER | нет | — |
| event_id | INTEGER | нет | events.id (RESTRICT) |
| reviewer_id | INTEGER | нет | users.id (RESTRICT) |
| decision | VARCHAR(20) | нет | — |
| comment | TEXT | да | — |
| created_at | TIMESTAMP WITH TIME ZONE | нет | — |

### event_topics

| Поле | Тип PostgreSQL | NULL | Связь |
|---|---|---|---|
| id | INTEGER | нет | — |
| event_id | INTEGER | нет | events.id (CASCADE) |
| topic_id | INTEGER | нет | topics.id (RESTRICT) |

### favorites

| Поле | Тип PostgreSQL | NULL | Связь |
|---|---|---|---|
| id | INTEGER | нет | — |
| user_id | INTEGER | нет | users.id (CASCADE) |
| event_id | INTEGER | нет | events.id (CASCADE) |
| created_at | TIMESTAMP WITH TIME ZONE | нет | — |

### plans

| Поле | Тип PostgreSQL | NULL | Связь |
|---|---|---|---|
| id | INTEGER | нет | — |
| user_id | INTEGER | нет | users.id (CASCADE) |
| event_id | INTEGER | нет | events.id (CASCADE) |
| reminder_minutes_before | INTEGER | да | — |
| reminder_read_for | TIMESTAMP WITH TIME ZONE | да | — |
| created_at | TIMESTAMP WITH TIME ZONE | нет | — |
| updated_at | TIMESTAMP WITH TIME ZONE | нет | — |

### registrations

| Поле | Тип PostgreSQL | NULL | Связь |
|---|---|---|---|
| id | INTEGER | нет | — |
| user_id | INTEGER | нет | users.id (RESTRICT) |
| event_id | INTEGER | нет | events.id (RESTRICT) |
| status | VARCHAR(20) | нет | — |
| registered_at | TIMESTAMP WITH TIME ZONE | нет | — |
| cancelled_at | TIMESTAMP WITH TIME ZONE | да | — |

### messages

| Поле | Тип PostgreSQL | NULL | Связь |
|---|---|---|---|
| id | INTEGER | нет | — |
| conversation_id | INTEGER | нет | conversations.id (CASCADE) |
| sender_id | INTEGER | нет | users.id (CASCADE) |
| client_id | VARCHAR(36) | нет | — |
| body | TEXT | нет | — |
| created_at | TIMESTAMP WITH TIME ZONE | нет | — |

## Pydantic-схемы

| Файл | Схемы и поля |
|---|---|
| achievements.py | **AttendanceWrite**: attended<br>**AttendanceRead**: event_id, user_id, attended, confirmed_at<br>**AchievementRead**: code, title, description, metric, target, progress, points, earned<br>**AchievementSummary**: user_id, name, attendance_count, olympiad_count, points, earned_count, rank, achievements<br>**LeaderboardEntry**: user_id, name, attendance_count, olympiad_count, points, earned_count, rank |
| auth.py | **RegisterRequest**: email, password, name, role<br>**LoginRequest**: email, password<br>**RefreshRequest**: refresh_token<br>**TokenPair**: access_token, refresh_token, token_type |
| cities.py | **CityCreate**: name, region, country_code, latitude, longitude<br>**CityUpdate**: name, region, country_code, latitude, longitude<br>**CityRead**: created_at, updated_at, name, region, country_code, latitude, longitude, id |
| common.py | **InputModel**: пустое тело {}<br>**ReadModel**: пустое тело {}<br>**PatchModel**: пустое тело {}<br>**Pagination**: page, limit<br>**Page**: items, total, page, limit<br>**Timestamps**: created_at, updated_at |
| events.py | **EventCreate**: title, description, category, city_id, school_id, cover_file_id, topic_ids, starts_at, ends_at, timezone, registration_deadline, format, place_name, address, latitude, longitude, online_url, min_grade, max_grade, min_age, max_age, price, capacity, registration_mode, registration_url, take_with_you<br>**EventUpdate**: title, description, category, city_id, school_id, cover_file_id, topic_ids, starts_at, ends_at, timezone, registration_deadline, format, place_name, address, latitude, longitude, online_url, min_grade, max_grade, min_age, max_age, price, capacity, registration_mode, registration_url, take_with_you<br>**EventRead**: created_at, updated_at, title, description, category, city_id, school_id, cover_file_id, topic_ids, starts_at, ends_at, timezone, registration_deadline, format, place_name, address, latitude, longitude, online_url, min_grade, max_grade, min_age, max_age, price, capacity, registration_mode, registration_url, take_with_you, id, organizer_id, status, cover_url, is_favorite, in_plans<br>**EventShort**: id, title, category, status, city_id, school_id, starts_at, ends_at, format, price, cover_url, is_favorite, in_plans, timezone, place_name, address, latitude, longitude, registration_deadline, registration_mode, min_grade, max_grade, min_age, max_age, capacity, topic_ids<br>**EventFilters**: search, city_id, school_id, category, topic_id, date_from, date_to, grade, age, format, price_min, price_max, place, sort, page, limit<br>**MapFilters**: search, city_id, school_id, category, topic_id, date_from, date_to, grade, age, format, price_min, price_max, place, sort, page, limit, west, south, east, north<br>**MapEventRead**: id, title, category, status, city_id, school_id, starts_at, ends_at, format, price, cover_url, is_favorite, in_plans, timezone, place_name, address, latitude, longitude, registration_deadline, registration_mode, min_grade, max_grade, min_age, max_age, capacity, topic_ids |
| favorites.py | **FavoriteRead**: event, created_at |
| files.py | **FileRead**: id, url, mime_type, size_bytes |
| locations.py | **LocationImport**: token<br>**LocationResult**: kind, name, label, region, address, latitude, longitude, token, source<br>**LocationSelection**: city, school |
| moderation.py | **RejectEventRequest**: comment<br>**ModerationRead**: id, event_id, reviewer_id, decision, comment, created_at |
| plans.py | **PlanWrite**: пустое тело {}<br>**PlanRead**: event, created_at<br>**PlanFilters**: page, limit, date_from, date_to |
| registrations.py | **RegistrationRead**: attended, event, participant_name, grade, id, user_id, event_id, status, registered_at, cancelled_at |
| schools.py | **SchoolCreate**: city_id, name, address, latitude, longitude<br>**SchoolUpdate**: city_id, name, address, latitude, longitude, is_active<br>**SchoolRead**: created_at, updated_at, city_id, name, address, latitude, longitude, id, is_active |
| topics.py | **TopicCreate**: name, slug<br>**TopicUpdate**: name, slug<br>**TopicRead**: created_at, updated_at, name, slug, id |
| users.py | **UserUpdate**: name, grade, city_id, school_id<br>**UserRead**: created_at, updated_at, id, email, name, role, grade, city_id, school_id, is_active<br>**InterestsUpdate**: topic_ids |

## crud

| Файл | Функции |
|---|---|
| cities.py | `create_city(db, data)`<br>`get_city(db, row_id, *, lock=False)`<br>`update_city(db, row, changes)`<br>`delete_city(db, row)`<br>`list_cities(db)` |
| common.py | `create(db, model, values)`<br>`get(db, model, row_id, *, lock=False)`<br>`update(db, row, changes)`<br>`remove(db, row)`<br>`page(db, stmt, pagination)` |
| events.py | `get_event(db, event_id, *, lock=False)`<br>`create_event(db, organizer_id, values)`<br>`filtered_query(filters, user=None)`<br>`list_events(db, filters, user=None)`<br>`list_map_events(db, filters, user=None)`<br>`update_event(db, event, changes)`<br>`set_event_status(db, event, status)`<br>`delete_event(db, event)` |
| favorites.py | `get_favorite(db, user_id, event_id)`<br>`add_favorite(db, user_id, event_id)`<br>`list_favorites(db, user_id, pagination)`<br>`remove_favorite(db, favorite)` |
| files.py | `create_file(db, data)`<br>`get_file(db, row_id, *, lock=False)`<br>`update_file(db, row, changes)`<br>`delete_file(db, row)` |
| interests.py | `get_user_interests(db, user_id)`<br>`replace_user_interests(db, user_id, topic_ids)`<br>`replace_event_topics(db, event_id, topic_ids)`<br>`event_topic_ids(db, event_id)` |
| moderation.py | `create_review(db, event_id, reviewer_id, decision, comment=None)`<br>`list_reviews(db, event_id)` |
| plans.py | `get_plan(db, user_id, event_id)`<br>`upsert_plan(db, user_id, event_id, data)`<br>`list_plans(db, user_id, filters)`<br>`remove_plan(db, plan)` |
| registrations.py | `get_registration(db, user_id, event_id)`<br>`count_registered(db, event_id)`<br>`create_registration(db, user_id, event_id)`<br>`cancel_registration(db, row)`<br>`list_event_registrations(db, event_id, pagination)`<br>`list_user_registrations(db, user_id, pagination)` |
| schools.py | `create_school(db, data)`<br>`get_school(db, row_id, *, lock=False)`<br>`update_school(db, row, changes)`<br>`delete_school(db, row)`<br>`list_schools(db, city_id, pagination)` |
| sessions.py | `create_session(db, user_id, token_hash, expires_at)`<br>`get_session_by_hash(db, token_hash, *, lock=False)`<br>`revoke_session(db, session)`<br>`revoke_user_sessions(db, user_id)` |
| topics.py | `create_topic(db, data)`<br>`get_topic(db, row_id, *, lock=False)`<br>`update_topic(db, row, changes)`<br>`delete_topic(db, row)`<br>`list_topics(db)` |
| users.py | `get_user(db, user_id, *, lock=False)`<br>`get_user_by_email(db, email)`<br>`create_user(db, data, password_hash)`<br>`update_user(db, user, changes)`<br>`deactivate_user(db, user)` |

## services

| Файл | Функции |
|---|---|
| achievements.py | `set_attendance(db, actor, event_id, user_id, attended)`<br>`ranked_query()`<br>`leaderboard(db, pagination)`<br>`summary(db, user_id)` |
| auth.py | `register(db, data)`<br>`issue_tokens(db, user)`<br>`login(db, data)`<br>`refresh(db, token)`<br>`logout(db, token)` |
| catalog.py | `edit_city(db, row_id, patch)`<br>`remove_city(db, row_id)`<br>`create_school(db, data)`<br>`edit_school(db, row_id, patch)`<br>`deactivate_school(db, row_id)`<br>`edit_topic(db, row_id, patch)`<br>`remove_topic(db, row_id)` |
| common.py | `require_row(db, model, row_id, *, lock=False)`<br>`validate(schema, data)`<br>`row_fields(row, schema)`<br>`check_location(db, city_id, school_id)`<br>`check_topics(db, topic_ids)` |
| events.py | `accessible_event(db, event_id, user=None, *, write=False, lock=False)`<br>`check_event_links(db, data, user)`<br>`database_values(data)`<br>`create(db, user, data)`<br>`edit(db, event_id, user, patch)`<br>`check_publishable(event, *, require_future=True)`<br>`change_status(db, event_id, user, action, comment=None)`<br>`remove(db, event_id, user)`<br>`serialize_many(db, rows, user=None, *, full=False)`<br>`detail(db, event, user=None)` |
| files.py | `inspect_image(content)`<br>`file_read(row)`<br>`upload(db, user, upload_file)`<br>`get_content(db, file_id, user)`<br>`remove(db, user, file_id)` |
| locations.py | `_fetch(params)`<br>`provider_search(params)`<br>`_norm(value)`<br>`_distance(lat, lon, lat2, lon2)`<br>`_result(payload, label, source='OpenStreetMap / Photon')`<br>`from_feature(feature, kind, city=None)`<br>`search(db, query, kind, city_id=None)`<br>`select_location(db, token)` |
| personal.py | `save_favorite(db, user, event_id)`<br>`save_plan(db, user, event_id, data)`<br>`personal_rows(db, rows, user)`<br>`register(db, user, event_id)`<br>`cancel_registration(db, user, event_id)` |
| users.py | `update_profile(db, user, data)`<br>`deactivate(db, user)`<br>`set_interests(db, user, topic_ids)` |

## Ручки

Кроме регистрации и входа, разделы с данными требуют Bearer-токен. Для изменения данных дополнительно проверяются роль и владелец.

| Метод | Путь | Назначение |
|---|---|---|
| GET | `/health` | Проверить доступность API и базы |
| POST | `/api/v1/auth/register` | Создать аккаунт ученика или организатора |
| POST | `/api/v1/auth/login` | Войти по email и паролю |
| POST | `/api/v1/auth/refresh` | Обновить токены; старые перестанут работать |
| POST | `/api/v1/auth/logout` | Отозвать сессию |
| GET | `/api/v1/me` | Мой профиль |
| DELETE | `/api/v1/me` | Деактивировать аккаунт и отозвать сессии |
| PATCH | `/api/v1/me` | Изменить профиль, сохранив пропущенные поля |
| GET | `/api/v1/me/interests` | Мои интересы |
| PUT | `/api/v1/me/interests` | Заменить список интересов |
| GET | `/api/v1/cities` | Список городов |
| POST | `/api/v1/cities` | Добавить город |
| GET | `/api/v1/cities/{city_id}` | Город по id |
| PATCH | `/api/v1/cities/{city_id}` | Изменить город |
| DELETE | `/api/v1/cities/{city_id}` | Удалить город без связанных данных |
| GET | `/api/v1/schools` | Активные школы, фильтр по городу |
| POST | `/api/v1/schools` | Добавить школу |
| GET | `/api/v1/schools/{school_id}` | Школа по id |
| PATCH | `/api/v1/schools/{school_id}` | Изменить школу |
| DELETE | `/api/v1/schools/{school_id}` | Деактивировать школу |
| GET | `/api/v1/topics` | Список тем |
| POST | `/api/v1/topics` | Добавить тему |
| GET | `/api/v1/topics/{topic_id}` | Тема по id |
| PATCH | `/api/v1/topics/{topic_id}` | Изменить тему |
| DELETE | `/api/v1/topics/{topic_id}` | Удалить неиспользуемую тему |
| GET | `/api/v1/events` | Лента и календарь: поиск, фильтры, сортировка |
| POST | `/api/v1/events` | Создать черновик |
| GET | `/api/v1/events/map` | Метки в видимой области карты |
| GET | `/api/v1/me/events` | Мои мероприятия, включая черновики |
| GET | `/api/v1/admin/events` | Все мероприятия для администратора, фильтр по статусу |
| GET | `/api/v1/events/{event_id}` | Полная карточка мероприятия |
| PATCH | `/api/v1/events/{event_id}` | Изменить мероприятие; опубликованное обновляется сразу |
| DELETE | `/api/v1/events/{event_id}` | Администратор удаляет любое событие; организатор — свой черновик |
| POST | `/api/v1/events/{event_id}/submit` | Отправить на модерацию |
| POST | `/api/v1/events/{event_id}/publish` | Опубликовать своё мероприятие без предварительного одобрения |
| POST | `/api/v1/events/{event_id}/reject` | Отклонить с комментарием |
| POST | `/api/v1/events/{event_id}/cancel` | Отменить мероприятие |
| GET | `/api/v1/events/{event_id}/moderation` | История решений модератора |
| GET | `/api/v1/me/favorites` | Моё избранное |
| PUT | `/api/v1/me/favorites/{event_id}` | Добавить в избранное без дубликатов |
| DELETE | `/api/v1/me/favorites/{event_id}` | Убрать из избранного |
| GET | `/api/v1/me/plans` | Личный календарь за период |
| PUT | `/api/v1/me/plans/{event_id}` | Добавить мероприятие в личный календарь |
| DELETE | `/api/v1/me/plans/{event_id}` | Убрать из планов |
| POST | `/api/v1/events/{event_id}/registrations` | Записаться участником |
| GET | `/api/v1/events/{event_id}/registrations` | Список участников своего мероприятия |
| DELETE | `/api/v1/events/{event_id}/registrations/me` | Отменить свою запись |
| GET | `/api/v1/me/registrations` | Мои записи на мероприятия |
| POST | `/api/v1/files` | Загрузить фотографию |
| GET | `/api/v1/files/{file_id}/content` | Изображение; чужие неопубликованные обложки скрыты |
| DELETE | `/api/v1/files/{file_id}` | Удалить неиспользуемую фотографию |
| GET | `/api/v1/locations/search` | Поиск по России: населённые пункты, школы, адреса |
| POST | `/api/v1/locations/select` | Сохранить выбранный результат в справочнике проекта |
| POST | `/api/v1/locations/schools/manual` | Организатор добавляет отсутствующую школу вручную |
| POST | `/api/v1/locations/cities/manual` | Организатор добавляет отсутствующий населённый пункт России |
| GET | `/api/v1/me/achievements` | My Achievements |
| GET | `/api/v1/achievements/leaderboard` | Leaderboard |
| GET | `/api/v1/users/{user_id}/achievements` | Participant Achievements |
| PUT | `/api/v1/events/{event_id}/attendance/{user_id}` | Confirm Attendance |
