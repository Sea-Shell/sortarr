---
type: Process
title: Sortarr Authentication
description: Google OAuth flow for accessing the YouTube Data API — authorization URL, code exchange, DB-backed credential storage, auto-refresh.
resource: https://github.com/Sea-Shell/sortarr/blob/main/src/sortarr/core/auth.py
tags: [sortarr, auth, oauth, youtube, google, database]
timestamp: 2026-07-12T22:30:00Z
---

# Why auth exists

`sortarr` acts on the user's own YouTube account (read subscriptions, write to
playlists), so it needs an OAuth2 access/refresh token for the YouTube Data API.
The [`YouTubeAPIClient`](/knowledge/concepts/architecture.md) uses those
credentials for every call.

# Credential inputs

- **Client config**: a Google OAuth client JSON (`SORTARR_CREDENTIALS_FILE`,
  default `client_secret.json`) contains the OAuth client ID and secret.
- **Token storage**: OAuth credentials are stored in the `oauth_credentials` 
  database table (single row, id=1) as a JSON blob containing token, refresh_token,
  token_uri, client_id, client_secret, and scopes. This replaces the legacy pickle
  file approach.

# Flow (core/auth.py + api/routes/auth.py)

1. `get_authorization_url()` builds the Google OAuth consent URL (redirect back
   to the configured redirect URI).
2. User authorizes; the app receives a code at the callback endpoint.
3. `handle_callback(code)` exchanges the code for OAuth credentials using
   `google-auth-oauthlib.flow.Flow`, then saves them to the database.
4. `get_credentials()` loads credentials from the database; `is_authenticated()`
   checks if valid credentials exist.
5. `get_http()` returns an `AuthorizedSession` with auto-refresh: if credentials
   are expired and a refresh_token exists, it refreshes the token and saves the
   updated credentials back to the database.

The OAuth manager (`OAuthManager`) handles the full lifecycle: authorization URL
generation, token exchange, database persistence, loading, clearing, and
auto-refresh on expiry.

# Database schema

```sql
CREATE TABLE IF NOT EXISTS oauth_credentials (
    id INTEGER PRIMARY KEY CHECK(id = 1),
    token_json TEXT NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);
```

The `token_json` column stores a JSON object with:
- `token`: Current access token
- `refresh_token`: Refresh token for obtaining new access tokens
- `token_uri`: Google's token endpoint URL
- `client_id`: OAuth client ID
- `client_secret`: OAuth client secret
- `scopes`: List of granted OAuth scopes

# Security

- Credentials are stored in the SQLite database with file permissions restricted
  to the app user (single-user K8s deployment on trusted infrastructure).
- Credentials are never logged — only high-level events like "OAuth credentials
  saved" or "OAuth token refreshed" appear in logs.
- The client secret file is loaded at startup and never stored in the database.

# Gotcha

`require_youtube()` (in `deps.py`) guards routes that need an authenticated
client — endpoints fail clearly if credentials are missing or expired rather
than erroring deep in a pipeline run.
