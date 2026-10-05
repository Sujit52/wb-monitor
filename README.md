# IP Cycler Admin

Secure FastAPI admin panel for the existing IP Cycler Firebase Realtime Database.

## Firebase paths used

- `config/enabled`
- `config/devices/<deviceId>/status`
- `config/devices/<deviceId>/uid`

The server uses Firebase Admin SDK credentials from environment variables. Never commit the service-account JSON or private key.

## Local run

```bash
uv sync
uv run fastapi dev
```

Open `http://127.0.0.1:8000`.

## Required environment variables

See `.env.example`.

For production, set these as hosting secrets/environment variables rather than committing `.env`.

## Important

The Android app remains a Firebase client. This admin server is only for your private control panel.
