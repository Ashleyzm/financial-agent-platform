# Public deployment

This guide describes how to share FinAgent temporarily and how to run it as a stable public service.

## Option A: temporary demo link

Use this only for a short review or classroom demonstration. Keep Docker Desktop and the terminal running:

```powershell
docker compose up -d --build --wait
cloudflared tunnel --url http://localhost:3000
```

`cloudflared` prints a random `https://*.trycloudflare.com` URL. Anyone with that URL can reach the application until the process stops. Quick Tunnels have no uptime guarantee and are not intended for production.

The Web gateway already proxies `/api/` requests to FastAPI, so only port `3000` needs to be tunneled. Do not tunnel PostgreSQL (`5432`), Redis (`6379`), or the API port (`8000`) separately.

Official reference: [Cloudflare Tunnel setup](https://developers.cloudflare.com/tunnel/setup/).

## Option B: stable public server

### 1. Prepare the server

Use a Linux server with:

- a public IPv4 address;
- at least 2 CPU cores, 4 GB RAM, and 20 GB storage for a small demo;
- Git, Docker Engine, and Docker Compose;
- inbound TCP port `80`, or `443` after HTTPS is configured.

### 2. Clone and configure

```bash
git clone https://github.com/Ashleyzm/financial-agent-platform.git
cd financial-agent-platform
cp .env.production.example .env.production
```

Edit `.env.production` before startup:

- replace `POSTGRES_PASSWORD` with a long random value;
- keep both providers set to `mock` for a safe public demo;
- if an external LLM is enabled, configure a restricted key and account quota;
- never commit `.env.production`.

### 3. Start the production profile

```bash
docker compose --env-file .env.production -f compose.prod.yaml up -d --build --wait
docker compose --env-file .env.production -f compose.prod.yaml ps
```

Visit `http://SERVER_PUBLIC_IP`. Only the Nginx Web gateway is published. The API, Worker, PostgreSQL, and Redis have no host ports in the production profile.

### 4. Configure a domain and HTTPS

Point a domain or subdomain to the server and place a TLS reverse proxy or a named Cloudflare Tunnel in front of port `80`. A stable Cloudflare Tunnel maps a public hostname to `http://localhost:80` without opening an inbound origin port.

Official reference: [Cloudflare Tunnel](https://developers.cloudflare.com/tunnel/).

### 5. Operate and update

```bash
docker compose --env-file .env.production -f compose.prod.yaml logs -f --tail=200
git pull --ff-only
docker compose --env-file .env.production -f compose.prod.yaml up -d --build --wait
```

Back up the `postgres_data` Docker volume before important upgrades.

## Security checklist

- Use strong and unique production passwords.
- Do not expose ports `5432`, `6379`, or `8000` publicly.
- Use HTTPS before entering any confidential information.
- Keep the default Mock providers for an anonymous public demo.
- Add authentication and task quotas before connecting a paid LLM key.
- Restrict cloud firewall rules and keep Docker/server packages updated.
- Treat task inputs and generated reports as untrusted content.

## Local network access

People on the same Wi-Fi/LAN may use `http://YOUR_LAN_IP:3000` while the local stack is running, provided Windows Firewall allows inbound TCP `3000`. This is not Internet deployment and should not be used on an untrusted network.
