# BRIDGE TV — Project Restored

> 🇷🇺 Русская версия ниже · 🇬🇧 English version below

**Live site / Сайт:** https://btvrestored.ru/  
**Repository / Репозиторий:** https://github.com/btvrestored/btvrestored.github.io

---

# 🇷🇺 Русская версия

> Фанатский проект по восстановлению и реконструкции атмосферы, визуального стиля, программ и эфирного опыта **BRIDGE TV**.

## О проекте

**BRIDGE TV — Project Restored** — статический веб-проект, посвящённый реконструкции сайта и эфирной инфраструктуры в стиле BRIDGE TV.

Проект объединяет:

- публичный сайт в стиле BRIDGE TV;
- live-видеоплеер на базе VK Video Live;
- систему сообщений зрителей, выводимых в эфир;
- архив программ и визуальных материалов;
- страницу повторов эфира;
- страницу заявок на клипы;
- двуязычный интерфейс RU/EN;
- административную панель для модерации и управления сообщениями;
- realtime-обновления через Supabase.

Проект представлен **BM-PR** и **не связан официально с BRIDGE MEDIA**.

## Сайт

Основной адрес:

**https://btvrestored.ru/**

| Страница | Назначение |
| --- | --- |
| `index.html` | Главная, live-плеер, сообщения зрителей и история |
| `shows.html` | Программы |
| `repeats.html` | Повторы эфира и архив VK Video |
| `identity.html` | Архив и материалы визуальной идентичности |
| `about.html` | О проекте |
| `order.html` | Заявки зрителей на клипы |
| `admin/` | Администрирование и модерация |

## Возможности

### Прямой эфир

Главная страница содержит текущую трансляцию VK Video Live:

- встроенный плеер;
- резервную прямую ссылку;
- адаптивный формат 16:9;
- поддержку полноэкранного режима и Picture-in-Picture.

### Сообщения зрителей

Зрители могут отправлять сообщения, которые после модерации могут появляться в эфире.

Поддерживаются:

- имя зрителя;
- текст сообщения;
- тип сообщения;
- предварительный просмотр;
- базовая защита от спама;
- фильтрация ненормативной лексики;
- задержка между отправками;
- статус модерации;
- сохранение статуса заявки.

Типы сообщений:

- Normal
- ⭐ VIP
- 💜 Glamour
- ⚡ Express

### Архив

Проект содержит отдельные страницы и ассеты для реконструированных и восстановленных материалов BRIDGE TV, включая оформление программ и исторические элементы визуальной идентичности.

### Языки

Публичные страницы поддерживают русский и английский языки. Выбранный язык сохраняется в `localStorage`.

## Админ-панель

Каталог `admin/` содержит интерфейс управления системой сообщений.

В него входят:

- авторизация администратора;
- live-лента сообщений;
- модерация входящих сообщений;
- одобрение и отклонение;
- повторная публикация сообщений;
- удаление сообщений;
- отображение статуса подключения;
- поддержка публичной chat/feed-системы.

Админ-панель использует тот же Supabase backend, что и публичная система сообщений.

## Данные и Supabase

**Supabase** используется для:

- авторизации;
- realtime-обновлений;
- публичных сообщений в эфир;
- входящих заявок зрителей;
- статусов модерации;
- проверки статусов заявок.

Основная клиентская обёртка:

`supabase-client.js`

Схема базы данных:

`admin/supabase-schema.sql`

Клиентская обёртка скрывает детали структуры таблиц от остальных частей frontend и предоставляет страницам API через `window.btv`.

## Структура проекта

```text
.
├── index.html              # Главная / прямой эфир
├── shows.html              # Программы
├── repeats.html            # Повторы эфира
├── identity.html           # Архив / визуальная идентичность
├── about.html              # О проекте
├── order.html              # Заявки на клипы
├── 404.html                # Страница 404
├── CNAME                   # Домен GitHub Pages
├── logo.png                # Логотип проекта
├── supabase-client.js      # Публичная Supabase-обёртка
│
├── admin/
│   ├── index.html          # Панель администратора
│   ├── chat.html           # Админский chat/on-air интерфейс
│   ├── receive.html        # Получение сообщений
│   ├── admin.css           # Стили админ-панели
│   ├── supabase-client.js  # Supabase-клиент админки
│   └── supabase-schema.sql # Схема базы данных
│
├── archive/
│   └── README.md           # Примечания к архивным материалам
│
├── shows/
│   └── *.jpg               # Оформление программ
│
└── .github/
    └── workflows/          # Конфигурация GitHub Actions
```

## Деплой

Репозиторий настроен для **GitHub Pages**.

Пользовательский домен задаётся через:

```text
CNAME
└── btvrestored.ru
```

Публичному frontend не требуется Node.js, npm или отдельная сборка. Сайт состоит преимущественно из HTML, CSS и JavaScript и может обслуживаться как обычный static site.

### Локальный запуск

Например:

```bash
python -m http.server 8080
```

После этого:

```text
http://localhost:8080/
```

## Настройка

Для собственного экземпляра проекта необходимо:

1. Создать или настроить Supabase project.
2. Применить `admin/supabase-schema.sql`.
3. Настроить Authentication и Row Level Security.
4. Указать URL Supabase project и publishable key в клиентской конфигурации.
5. Настроить VK Video Live stream/embed URL.
6. При необходимости указать собственный GitHub Pages domain в `CNAME`.

### Безопасность

**Не размещайте** в frontend:

- Supabase service-role keys;
- пароли;
- приватные токены;
- другие секретные credentials.

В браузере должны использоваться только публичные/publishable credentials. Доступ к базе необходимо защищать соответствующими Supabase RLS policies.

Локальный `.env` обычно должен оставаться вне Git и быть добавлен в `.gitignore`.

## Разработка

Проект намеренно остаётся лёгким:

- framework для публичных страниц не требуется;
- HTML/CSS/JavaScript находятся непосредственно в репозитории;
- внешние сервисы используются там, где это необходимо;
- публичные страницы рассчитаны на работу как static GitHub Pages content.

При изменении системы сообщений следует сохранять совместимость API `window.btv` со страницами, которые его используют.

## Credits

**BRIDGE TV — Project Restored**  
Presented by **BM-PR**.

Это независимый проект по восстановлению и реконструкции и **не является официальным проектом BRIDGE MEDIA**.

BRIDGE TV, исторический брендинг, названия программ и визуальные материалы принадлежат соответствующим правообладателям.

## Лицензия

Если для отдельного файла не указано иное, код и материалы репозитория являются частью проекта **BRIDGE TV — Project Restored**.

Сторонние названия, торговые марки, логотипы, видео, музыка, фотографии и исторические материалы остаются собственностью соответствующих правообладателей.

Дополнительные сведения об авторстве и лицензировании смотрите в отдельных файлах и материалах.

---

# 🇬🇧 English version

> A fan-made restoration and reconstruction project inspired by the visual style, programs and on-air experience of **BRIDGE TV**.

## About

**BRIDGE TV — Project Restored** is a static web project built around a recreated BRIDGE TV-style website and accompanying live/on-air infrastructure.

The project combines:

- a BRIDGE TV-inspired public website;
- a live video player powered by VK Video Live;
- an on-screen viewer message system;
- an archive of programs and visual materials;
- broadcast repeat pages;
- a clip request page;
- a bilingual RU/EN interface;
- an administration panel for moderation and on-air messages;
- Supabase realtime updates.

The project is presented by **BM-PR** and is **not affiliated with BRIDGE MEDIA**.

## Website

Main address:

**https://btvrestored.ru/**

| Page | Description |
| --- | --- |
| `index.html` | Main page, live player, viewer messages and history |
| `shows.html` | Programs / shows |
| `repeats.html` | Broadcast repeats and VK Video archive |
| `identity.html` | Archive and visual identity materials |
| `about.html` | About the project |
| `order.html` | Viewer clip request page |
| `admin/` | Administration and moderation interface |

## Features

### Live broadcast

The main page embeds the current VK Video Live stream:

- embedded player;
- direct-link fallback;
- responsive 16:9 layout;
- fullscreen and Picture-in-Picture support.

### Viewer messages

Visitors can submit messages that may appear on the broadcast after moderation.

The system supports:

- viewer name;
- message text;
- message type;
- preview before sending;
- basic anti-spam validation;
- profanity filtering;
- submission cooldown;
- moderation status;
- persistent request status.

Available message types:

- Normal
- ⭐ VIP
- 💜 Glamour
- ⚡ Express

### Archive

The project contains dedicated pages and assets for reconstructed and restored BRIDGE TV material, including program artwork and historical-style identity assets.

### Language support

The public pages support Russian and English. The selected language is stored in `localStorage`.

## Admin panel

The `admin/` directory contains the management interface for the viewer-message system.

It includes:

- administrator authentication;
- live message feed;
- inbox moderation;
- approve / reject actions;
- message repetition;
- message deletion;
- connection status;
- public chat/feed support.

The admin side uses the same Supabase backend as the public viewer-message interface.

## Data layer and Supabase

**Supabase** is used for:

- authentication;
- realtime updates;
- public on-air messages;
- viewer inbox submissions;
- moderation status;
- request status polling.

Main client wrapper:

`supabase-client.js`

Database schema:

`admin/supabase-schema.sql`

The client wrapper keeps the rest of the frontend independent from the underlying database column naming and exposes the `window.btv` API used by the pages.

## Project structure

```text
.
├── index.html              # Main page / live broadcast
├── shows.html              # Programs
├── repeats.html            # Broadcast repeats
├── identity.html           # Archive / visual identity
├── about.html              # About the project
├── order.html              # Clip request page
├── 404.html                # Custom 404 page
├── CNAME                   # GitHub Pages custom domain
├── logo.png                # Project logo
├── supabase-client.js      # Public Supabase client wrapper
│
├── admin/
│   ├── index.html          # Admin dashboard
│   ├── chat.html           # Admin chat/on-air interface
│   ├── receive.html        # Message receiving interface
│   ├── admin.css           # Admin styles
│   ├── supabase-client.js  # Admin Supabase client
│   └── supabase-schema.sql # Database schema
│
├── archive/
│   └── README.md           # Archive asset notes
│
├── shows/
│   └── *.jpg               # Program artwork
│
└── .github/
    └── workflows/          # GitHub Actions configuration
```

## Deployment

The repository is configured as a **GitHub Pages** site.

The custom domain is defined by:

```text
CNAME
└── btvrestored.ru
```

No Node.js build step, npm or separate package manager is required for the public frontend. The site is primarily made from HTML, CSS and JavaScript and can be served as static files.

### Local preview

For example:

```bash
python -m http.server 8080
```

Then open:

```text
http://localhost:8080/
```

## Configuration

To create another instance of the project:

1. Create/configure a Supabase project.
2. Apply `admin/supabase-schema.sql`.
3. Configure Authentication and Row Level Security.
4. Set the Supabase project URL and publishable key in the client configuration.
5. Configure the VK Video Live stream/embed URL.
6. Set the desired GitHub Pages custom domain in `CNAME`.

### Security

**Do not put** the following into frontend code:

- Supabase service-role keys;
- passwords;
- private tokens;
- other secret credentials.

Only public/publishable client credentials should be exposed to the browser. Database access must be protected with appropriate Supabase RLS policies.

A local `.env` file should normally remain untracked and be excluded through `.gitignore`.

## Development notes

The project intentionally keeps the frontend lightweight:

- no framework is required for the public pages;
- HTML/CSS/JavaScript are kept directly in the repository;
- external services are used only where necessary;
- public pages are designed to work as static GitHub Pages content.

When changing the public message system, keep the API exposed by `window.btv` compatible with the pages that consume it.

## Credits

**BRIDGE TV — Project Restored**  
Presented by **BM-PR**.

This is an independent restoration / reconstruction project and is **not affiliated with BRIDGE MEDIA**.

BRIDGE TV and related historical branding, programming and visual materials belong to their respective rights holders.

## License

Unless a file states otherwise, the repository contains project-specific code and assets created for **BRIDGE TV — Project Restored**.

Third-party names, trademarks, logos, videos, music, photographs and historical materials remain the property of their respective owners.

See individual files and assets for any additional licensing or attribution information.
