# BRIDGE TV — Project Restored

> A fan-made restoration / reconstruction project inspired by the visual style, programs and on-air experience of **BRIDGE TV**.

**Live site:** https://btvrestored.ru/  
**Repository:** https://github.com/btvrestored/btvrestored.github.io

---

## About

**BRIDGE TV — Project Restored** is a static web project built around a recreated BRIDGE TV-style website and an accompanying live/on-air infrastructure.

The project combines:

- a BRIDGE TV-inspired public website;
- a live video player powered by VK Video Live;
- an on-screen viewer message system;
- an archive of programs and visual materials;
- broadcast repeat placeholders;
- a clip request page;
- a bilingual RU/EN interface;
- an administration panel for moderation and on-air messages;
- Supabase-backed realtime data for the message/inbox system.

The project is presented by **BM-PR** and is **not affiliated with BRIDGE MEDIA**.

---

## Website

The public website is available at:

**https://btvrestored.ru/**

Main sections:

| Page | Description |
| --- | --- |
| `index.html` | Main page, live player, viewer messages and history |
| `shows.html` | Programs / shows |
| `repeats.html` | Broadcast repeats and VK Video archive |
| `identity.html` | Archive and visual identity materials |
| `about.html` | About the project |
| `order.html` | Viewer clip request page |
| `admin/` | Administration and moderation interface |

---

## Features

### Live broadcast

The main page embeds the current VK Video Live stream:

- embedded player;
- direct-link fallback;
- responsive 16:9 layout;
- fullscreen and picture-in-picture support.

### Viewer messages

Visitors can send messages that can appear on the broadcast after moderation.

The system supports:

- viewer name;
- message text;
- message type;
- preview before sending;
- basic anti-spam validation;
- profanity filtering;
- cooldown between submissions;
- moderation status;
- persistent request status.

Available message types include:

- Normal
- ⭐ VIP
- 💜 Glamour
- ⚡ Express

### Archive

The project contains dedicated pages and assets for reconstructed / restored BRIDGE TV visual material, including program artwork and historical-style identity assets.

### Language support

The public pages include Russian and English localization with the selected language stored in `localStorage`.

---

## Admin panel

The `admin/` directory contains the management interface used for the on-air message system.

It includes:

- administrator authentication;
- live message feed;
- inbox moderation;
- approve / reject actions;
- repeat messages;
- delete messages;
- connection status;
- public chat/feed support.

The admin side uses the same Supabase backend as the public viewer-message interface.

---

## Data layer

The project uses **Supabase** for:

- authentication;
- realtime message updates;
- public on-air messages;
- viewer inbox submissions;
- moderation status;
- request status polling.

The main client wrapper is:

`supabase-client.js`

The database schema used by the admin interface is documented in:

`admin/supabase-schema.sql`

The client wrapper keeps the rest of the frontend independent from the underlying database column naming and exposes the `window.btv` API used by the pages.

---

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
├── CNAME                   # Custom GitHub Pages domain
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

---

## Deployment

The repository is configured as a **GitHub Pages** site.

The custom domain is defined by:

```text
CNAME
└── btvrestored.ru
```

There is no Node.js build step or package manager required for the public frontend. The site is primarily made from HTML, CSS and JavaScript and can be served as static files.

### Local preview

A simple static HTTP server is enough.

For example, with Python:

```bash
python -m http.server 8080
```

Then open:

```text
http://localhost:8080/
```

---

## Configuration

The public frontend expects the Supabase client configuration to be available to the browser.

Before deploying a fork or a new instance:

1. Create/configure a Supabase project.
2. Apply the database schema from `admin/supabase-schema.sql`.
3. Configure authentication and Row Level Security according to the intended deployment.
4. Update the Supabase project URL and publishable key in the client configuration.
5. Configure the VK Video Live stream/embed URL.
6. Set the desired GitHub Pages custom domain in `CNAME`.

### Security

Do **not** put Supabase service-role keys, passwords or other private credentials into frontend JavaScript.

Only public/publishable client credentials should be exposed to the browser. Database access must be protected with appropriate Supabase RLS policies.

If a local `.env` file is used for development, it should normally remain untracked and be excluded through `.gitignore`.

---

## Development notes

This project intentionally keeps the frontend lightweight:

- no framework is required for the public pages;
- HTML/CSS/JavaScript are kept directly in the repository;
- external services are used only where necessary;
- the public pages are designed to work as static GitHub Pages content.

When changing the public message system, keep the API exposed by `window.btv` compatible with the pages that consume it.

---

## Credits

**BRIDGE TV — Project Restored**  
Presented by **BM-PR**.

This is an independent restoration / reconstruction project and is **not affiliated with BRIDGE MEDIA**.

BRIDGE TV and related historical branding, programming and visual materials belong to their respective rights holders.

---

## License

Unless a file states otherwise, the repository contains project-specific code and assets created for **BRIDGE TV — Project Restored**.

Third-party names, trademarks, logos, videos, music, photographs and historical materials remain the property of their respective owners.

See individual files and assets for any additional licensing or attribution information.
