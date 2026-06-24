---
type: Process
title: Sortarr Authentication
description: Google OAuth flow for accessing the YouTube Data API — authorization URL, code exchange, credential storage, device/headless mode.
resource: https://github.com/Sea-Shell/sortarr/blob/main/src/sortarr/core/auth.py
tags: [sortarr, auth, oauth, youtube, google]
timestamp: 2026-06-24T10:00:00Z
---

# Why auth exists

`sortarr` acts on the user's own YouTube account (read subscriptions, write to
playlists), so it needs an OAuth2 access/refresh token for the YouTube Data API.
The [`YouTubeAPIClient`](/knowledge/concepts/architecture.md) uses those
credentials for every call.

# Credential inputs

- **Client config**: a Google OAuth client JSON (`SORTARR_CREDENTIALS_FILE`,
  default `client_secret.json`), or stored in the DB. `get_client_config()` /
  `_extract client_id and client_secret from the credentials JSON in DB`.
- **Token storage**: `SORTARR_PICKLE_FILE` (default `credentials.pickle`) holds
  the obtained OAuth credentials. See [runtime config](/knowledge/concepts/runtime-config.md).

# Flow (core/auth.py + api/routes/auth.py)

1. `get_authorization_url()` builds the Google OAuth consent URL (redirect back
   to `public_url`).
2. User authorizes; the app receives a code.
3. `exchange_code_for_tokens(code)` swaps it for OAuth credentials, which are
   persisted (pickle/DB).
4. `load_credentials()` / `credentials_status()` restore and report auth state;
   `GET /api/auth/status` surfaces it to the UI.

A device-style flow is exposed over HTTP: `POST /api/auth/device` starts it and
`POST /api/auth/poll` waits for completion — see [API](/knowledge/concepts/api.md).

# Headless mode

Set `SORTARR_NO_WEBBROWSER=true` to skip launching a local browser (for servers
/ containers); complete the consent step manually with the printed URL.

# Gotcha

`require_youtube()` (in `deps.py`) guards routes that need an authenticated
client — endpoints fail clearly if credentials are missing or expired rather
than erroring deep in a pipeline run.
