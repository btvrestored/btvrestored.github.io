# Supabase migration staging

This branch is a staged migration; the live `main` branch and Firebase pages are not changed.

## Files
- `supabase/migrations/001_initial_schema.sql`: tables, RLS policies, admin allow-list, and Realtime publication.
- `js/supabase-config.js`: browser-safe project URL and publishable key.

## Apply database schema
1. In Supabase Dashboard, confirm the Auth user with UID `bf8a8fdc-52ae-4626-b47c-5ef802296001` exists.
2. Open SQL Editor and run `supabase/migrations/001_initial_schema.sql`.
3. Confirm `admin_users` contains exactly the intended admin UUID.
4. In Authentication settings, disable public signups if only the owner should log in; create/invite the admin account through the Dashboard.
5. Enable email confirmation and use a strong unique password.

## Important
- This is not yet a complete front-end switch. Existing Firebase pages continue using Firebase until their code is deliberately migrated.
- Never put a Supabase service_role or secret key in this repository.
- The public visitor can insert only pending inbox records. Public users cannot read the inbox or write published messages.
- Admin authorization is enforced by the admin_users allow-list and RLS, not by hiding controls in the browser.
- Basic RLS does not prevent spam/flooding. Before opening public submissions, add server-side rate limiting (for example, an Edge Function with CAPTCHA verification) and validate inputs server-side.
- Test with a non-admin session: reading messages should work; reading/modifying inbox and inserting into messages should fail.
- Test OBS using only the publishable key and public SELECT policy on messages.
