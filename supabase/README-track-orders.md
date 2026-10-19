# Track Orders Edge Function (Neon + Supabase)

This function is deployed into the existing BTV Supabase project. It replaces the suspended Deno Deploy API; the Neon database remains unchanged.

## URLs

- BTV: `https://cmjtxlevjnwugeyttexa.supabase.co/functions/v1/track-orders-api`
- RTV: `https://fmwagmqysszshcvaddwo.supabase.co/functions/v1/track-orders-api`

Routes: `/healthz`, `/api/requests` (POST), `/api/catalog/search` (POST), `/api/admin/requests` (GET), and `/api/admin/requests/:uuid/review` (POST).

## Secrets to add in each existing project

Open **Edge Functions → Secrets** and add:

- `DATABASE_URL`: Neon pooled/serverless connection string.
- `TRACK_REQUEST_HASH_SALT`: the existing random salt; at least 24 characters.
- `TRACK_ORDERS_CHANNEL`: `btv` in BTV; `rtv` in RTV.
- `TRACK_ORDERS_AUTH_PUBLISHABLE_KEY`: publishable key from that same project's existing Auth configuration.
- Optional `DISCOGS_TOKEN`: only if you want Discogs search.

The Supabase runtime supplies `SUPABASE_URL`; the function uses it to validate the current project's access tokens. Do not add any service-role or secret API key to the frontend.

## Deploy in the Dashboard

1. Open your existing BTV Supabase project; do not create another project.
2. Open **Edge Functions** and create a function named `track-orders-api`.
3. Copy the contents of `index.ts` in this folder into the editor and deploy.
4. Under **Edge Functions → Secrets**, add the required secrets above.
5. Ensure gateway JWT verification is disabled for this function (`verify_jwt = false`). Anonymous form submissions need to reach the handler; the function independently enforces the site Origin and verifies Supabase Auth on admin routes.
6. Repeat steps 1–5 in the existing RTV project, setting `TRACK_ORDERS_CHANNEL=rtv`.
7. Test each URL with `/healthz`; expected fields include `databaseConnected: true`, `schemaReady: true`, `rateLimitSaltConfigured: true`, `authConfigured: true`, `channelConfigured: true`, and the matching `channel`.

## Database / security

The function uses the existing Neon tables: `track_requests`, `track_request_admins`, `track_request_rate_limits`, `track_catalog_cache`, and `track_catalog_api_state`. Do not run destructive SQL or create another Neon project.

New submissions always enter `pending`. Only direct HTTPS YouTube/VK video URLs are accepted. Public routes are throttled (5 submissions, 20 catalog searches per 10-minute identity/channel window); MusicBrainz requests have a shared 1.1-second database throttle and 12-hour cache. Moderator routes validate the bearer token with this project's Supabase Auth endpoint and require an active matching row in Neon.
