# Invoice System

Бэк учётной системы для формирования счетов-фактур по доходным и НДС проводкам на продажи услуг банка

## Стек

- Python 3.12+
- FastAPI
- PostgreSQL 16
- SQLAlchemy 2.0 
- Alembic 
- RabbitMQ 3.13

### 1. Клонировать репозиторий

```bash
git clone <url>
cd invoice-system

### 2. Поднять инфраструктуру
Требуется установленный Docker Desktop

``` bash
docker-compose up -d
```
Это поднимет:

PostgreSQL на порту 5432  
RabbitMQ на порту 5672 (UI: http://localhost:15672, логин: rabbit_user / rabbit_pass)

### 3. Установить зависимости

```bash
cd backend
python -m venv venv
```
Активировать виртуальное окружение:

Windows: venv\Scripts\activate  
Mac/Linux: source venv/bin/activate

```bash
pip install -r requirements.txt
```

### 4. Применить миграции

```bash
alembic upgrade head
```

### 5. Запустить сервер

```bash
uvicorn app.main:app --reload --log-level debug
```
Сервер доступен по адресу http://localhost:8000.

API документация  
После запуска сервера:

Swagger: http://localhost:8000/docs

### 6. Примеры запросов

Регистрация

```bash
POST /api/v1/auth/register
Content-Type: application/json

{
  "email": "user@example.com",
  "username": "user",
  "password": "password123",
  "full_name": "Иванов Иван"
}
```

Авторизация

```bash
POST /api/v1/auth/login
Content-Type: application/json

{
  "username": "user",
  "password": "password123"
}
```

Ответ:

```json
{
  "access_token": "eyJhbGciOiJIUzI1...",
  "token_type": "bearer"
}
```

Получение профиля

```bash
GET /api/v1/auth/me
Authorization: Bearer <access_token>
```

Пример: создать проводку через REST

```bash
POST /api/v1/transactions
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "external_id": "ABS-001",
  "transaction_date": "2026-05-13",
  "transaction_type": "income",
  "amount": "15000.00",
  "contract_number": "DOG-2026-201",
  "service_code": "ACQUIRING",
  "service_name": "Эквайринг",
  "vat_rate": "20.00",
  "link_key": "DOG-2026-201-2026-05-13",
  "country_code": "RU"
}
```

Пример: ручной запуск связывания проводок (сборка с/ф из пары income+vat)

```bash
POST /api/v1/sync/match-transactions
Authorization: Bearer <access_token>
```

Пример: подтверждение с/ф

```bash
POST /api/v1/invoices/{invoice_id}/approve
Authorization: Bearer <access_token>
```

Пример: отправка подтверждённой с/ф в исходящую очередь (ЭДО)

```bash
POST /api/v1/sync/send-invoice/{invoice_id}
Authorization: Bearer <access_token>
```

## Эндпоинты

| Метод | URL | Описание | Авторизация |
|-------|-----|----------|-------------|
| GET | `/health` | Проверка работоспособности | Нет |
| POST | `/api/v1/auth/register` | Регистрация пользователя | Нет |
| POST | `/api/v1/auth/login` | Авторизация, получение JWT | Нет |
| GET | `/api/v1/auth/me` | Текущий пользователь | Bearer token |
| POST | `/api/v1/data-load/standard` | Стандартная загрузка из АБС | Bearer token |
| POST | `/api/v1/data-load/by-date` | Загрузка за конкретный день | Bearer token |
| POST | `/api/v1/data-load/by-account` | Загрузка по счёту | Bearer token |
| GET | `/api/v1/data-load/log` | Журнал загрузок | Bearer token |
| GET | `/api/v1/data-load/log/last` | Последняя успешная загрузка | Bearer token |
| GET | `/api/v1/data-load/log/{id}` | Статус загрузки по ID | Bearer token |
| GET | `/api/v1/references/regional-centers` | Список региональных центров | Bearer token |
| POST | `/api/v1/references/regional-centers` | Создать региональный центр | Bearer token |
| PATCH | `/api/v1/references/regional-centers/{id}` | Редактировать региональный центр | Bearer token |
| DELETE | `/api/v1/references/regional-centers/{id}` | Удалить региональный центр | Bearer token |
| GET | `/api/v1/references/branches` | Список отделений | Bearer token |
| POST | `/api/v1/references/branches` | Создать отделение | Bearer token |
| GET | `/api/v1/references/branches/{id}` | Получить отделение по ID | Bearer token |
| PATCH | `/api/v1/references/branches/{id}` | Редактировать отделение | Bearer token |
| DELETE | `/api/v1/references/branches/{id}` | Удалить отделение | Bearer token |
| GET | `/api/v1/references/vat-accounts` | Список счетов НДС | Bearer token |
| POST | `/api/v1/references/vat-accounts` | Добавить счёт НДС | Bearer token |
| GET | `/api/v1/references/vat-accounts/{id}` | Получить счёт НДС по ID | Bearer token |
| PATCH | `/api/v1/references/vat-accounts/{id}` | Редактировать счёт НДС | Bearer token |
| DELETE | `/api/v1/references/vat-accounts/{id}` | Удалить счёт НДС | Bearer token |
| GET | `/api/v1/references/income-accounts` | Список счетов доходов | Bearer token |
| POST | `/api/v1/references/income-accounts` | Добавить счёт доходов | Bearer token |
| GET | `/api/v1/references/income-accounts/{id}` | Получить счёт доходов по ID | Bearer token |
| PATCH | `/api/v1/references/income-accounts/{id}` | Редактировать счёт доходов | Bearer token |
| DELETE | `/api/v1/references/income-accounts/{id}` | Удалить счёт доходов | Bearer token |
| GET | `/api/v1/references/responsibles` | Список ответственных | Bearer token |
| POST | `/api/v1/references/responsibles` | Добавить ответственного | Bearer token |
| GET | `/api/v1/references/responsibles/{id}` | Получить ответственного по ID | Bearer token |
| PATCH | `/api/v1/references/responsibles/{id}` | Редактировать ответственного | Bearer token |
| DELETE | `/api/v1/references/responsibles/{id}` | Удалить ответственного | Bearer token |
| GET | `/api/v1/counterparties` | Список контрагентов | Bearer token |
| POST | `/api/v1/counterparties` | Создать контрагента | Bearer token |
| GET | `/api/v1/counterparties/{id}` | Получить контрагента по ID | Bearer token |
| PATCH | `/api/v1/counterparties/{id}` | Редактировать контрагента | Bearer token |
| DELETE | `/api/v1/counterparties/{id}` | Удалить контрагента | Bearer token |
| GET | `/api/v1/mock/abs/counterparties` | Мок АБС: список контрагентов | Bearer token |
| POST | `/api/v1/sync/counterparties` | Ручной запуск синхронизации контрагентов (в фоне) | Bearer token |
| GET | `/api/v1/transactions` | Реестр проводок (фильтры/пагинация/сортировка) | Bearer token |
| POST | `/api/v1/transactions` | Создать одну проводку (тестовый режим) | Bearer token |
| POST | `/api/v1/transactions/batch` | Создать пачку проводок (тестовый режим) | Bearer token |
| GET | `/api/v1/transactions/{id}` | Получить проводку по ID | Bearer token |
| GET | `/api/v1/transactions/by-link-key/{link_key}` | Получить проводки по ключу связки | Bearer token |
| POST | `/api/v1/sync/match-transactions` | Ручной запуск связывания проводок (сборка СФ) | Bearer token |
| GET | `/api/v1/invoices` | Реестр счетов‑фактур (фильтры/пагинация/сортировка) | Bearer token |
| GET | `/api/v1/invoices/{id}` | Карточка счета‑фактуры | Bearer token |
| PATCH | `/api/v1/invoices/{id}` | Редактирование счета‑фактуры (без смены статуса) | Bearer token |
| POST | `/api/v1/invoices/{id}/approve` | Подтвердить счет‑фактуру (approved) | Bearer token |
| POST | `/api/v1/invoices/{id}/cancel` | Отменить счет‑фактуру (cancelled) | Bearer token |
| POST | `/api/v1/invoices/{id}/return-to-draft` | Вернуть approved → draft | Bearer token |
| POST | `/api/v1/sync/send-invoice/{invoice_id}` | Отправить одну approved СФ в очередь ЭДО | Bearer token |
| POST | `/api/v1/sync/send-approved-invoices` | Отправить пачку approved СФ в очередь ЭДО | Bearer token |

## Фильтры журнала загрузки

| Параметр | Значения | Описание |
|----------|----------|----------|
| `period` | `hour` / `day` / `week` / `month` / `three_months` | Период фильтрации |
| `status` | `in_progress` / `success` / `error` | Статус загрузки |
| `load_type` | `standard` / `by_date` / `by_account` | Тип загрузки |
| `page` | число от 1 | Номер страницы |
| `page_size` | число от 1 до 100 | Размер страницы |
| `sort_by` | имя поля | Поле сортировки |
| `sort_order` | `ASC` / `DESC` | Направление сортировки |

## Фильтры справочников

| Справочник | Параметры фильтрации |
|------------|---------------------|
| Счета НДС | `regional_center_id`, `branch_id`, `account_number`, `sort_by`, `sort_order` |
| Счета доходов | `regional_center_id`, `branch_id`, `account_number`, `sort_by`, `sort_order` |
| Ответственные | `regional_center_id`, `user_id`, `sort_by`, `sort_order` |
| Отделения | `regional_center_id`, `sort_by`, `sort_order` |
| Региональные центры | `sort_by`, `sort_order` |
| Контрагенты | `inn`, `full_name`, `sort_by`, `sort_order` |
| Проводки | `transaction_type`, `status`, `link_key`, `branch_id`, `counterparty_id`, `date_from`, `date_to`, `sort_by`, `sort_order` |
| Счета‑фактуры | `status`, `branch_id`, `counterparty_id`, `date_from`, `date_to`, `sort_by`, `sort_order` |

## Статусы загрузки

| Статус | Описание                  |
|--------|---------------------------|
| `in_progress` | Загрузка в процессе    |
| `success` | Загрузка завершена успешно |
| `error` | Загрузка завершена с ошибкой |

## Статусы счетов‑фактур

| Статус | Описание |
|--------|----------|
| `draft` | Черновик |
| `approved` | Подтверждён |
| `sent` | Отправлен в ЭДО (в исходящую очередь) |
| `cancelled` | Отменён |

## Очереди RabbitMQ

- Входящие проводки: `abs.transactions.incoming`
- Исходящие СФ (ЭДО): `edo.invoices.outgoing`

Пример входного сообщения для очереди `abs.transactions.incoming` (JSON payload):

```json
{
  "external_id": "RMQ-201",
  "transaction_date": "2026-05-13",
  "transaction_type": "income",
  "amount": "15000.00",
  "contract_number": "DOG-2026-201",
  "service_code": "ACQUIRING",
  "service_name": "Эквайринг",
  "vat_rate": "20.00",
  "link_key": "DOG-2026-201-2026-05-13",
  "country_code": "RU"
}
```

## Структура БД

| Таблица | Описание                    |
|---------|-----------------------------|
| `users` | Пользователи системы        |
| `roles` | Роли                        |
| `user_roles` | Связь пользователей и ролей |
| `regional_centers` | Региональные центры         |
| `branches` | Отделения банка             |
| `vat_accounts` | Счета НДС                   |
| `income_accounts` | Счета доходов               |
| `responsibles` | Ответственные по СФ         |
| `counterparties` | Контрагенты                 |
| `transactions` | Проводки АБС                |
| `data_load_logs` | Журнал загрузки из АБС      |
| `invoice_drafts` | Проекты счетов‑фактур       |
| `invoices` | Оформленные счета‑фактуры   |

## Тестовые данные

Все тестовые пользователи логинятся с паролем `Test12345!`

| Логин | Роли |
|-------|------|
| `admin` | Администратор |
| `buhgalter` | Бухгалтер |
| `superadmin` | Администратор + Бухгалтер |
| `factoring1` | Сотрудник факторинга |
| `factoring2` | Сотрудник факторинга |
| `acquiring1` | Сотрудник эквайринга |
| `manager1` | Сотрудник эквайринга |
```