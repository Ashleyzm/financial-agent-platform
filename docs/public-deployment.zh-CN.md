# 公网部署指南

本指南介绍如何临时分享 FinAgent，以及如何将其部署为稳定的公网服务。

## 方案 A：临时演示链接

该方式仅适合课堂展示或短期评审。Docker Desktop 和终端必须持续运行：

```powershell
docker compose up -d --build --wait
cloudflared tunnel --url http://localhost:3000
```

`cloudflared` 会输出一个随机的 `https://*.trycloudflare.com` 地址。进程停止前，任何拿到链接的人都可以打开平台。Quick Tunnel 不保证可用性，不适合作为正式生产服务。

Web 网关已经把 `/api/` 请求转发给 FastAPI，因此只需要映射 `3000` 端口。不要单独映射 PostgreSQL（`5432`）、Redis（`6379`）或 API（`8000`）端口。

官方资料：[Cloudflare Tunnel 配置](https://developers.cloudflare.com/tunnel/setup/)。

## 方案 B：稳定公网服务器

### 1. 准备服务器

建议小型演示服务器具备：

- 公网 IPv4 地址；
- 至少 2 核 CPU、4 GB 内存和 20 GB 存储；
- Git、Docker Engine 与 Docker Compose；
- 开放 TCP `80`，配置 HTTPS 后使用 `443`。

### 2. 下载并配置项目

```bash
git clone https://github.com/Ashleyzm/financial-agent-platform.git
cd financial-agent-platform
cp .env.production.example .env.production
```

启动前编辑 `.env.production`：

- 将 `POSTGRES_PASSWORD` 替换为足够长的随机密码；
- 公开演示建议保持两个 Provider 都为 `mock`；
- 如果启用外部 LLM，应设置受限 Key 和账户额度；
- 绝对不要提交 `.env.production`。

### 3. 启动生产环境

```bash
docker compose --env-file .env.production -f compose.prod.yaml up -d --build --wait
docker compose --env-file .env.production -f compose.prod.yaml ps
```

访问 `http://服务器公网IP`。生产配置只公开 Nginx Web 网关，API、Worker、PostgreSQL 和 Redis 均不映射主机端口。

### 4. 配置域名与 HTTPS

将域名或子域名解析到服务器，并在 `80` 端口前增加 TLS 反向代理；也可以使用 Cloudflare Named Tunnel，将公网域名映射到 `http://localhost:80`，无需开放源站入站端口。

官方资料：[Cloudflare Tunnel](https://developers.cloudflare.com/tunnel/)。

### 5. 运维与更新

```bash
docker compose --env-file .env.production -f compose.prod.yaml logs -f --tail=200
git pull --ff-only
docker compose --env-file .env.production -f compose.prod.yaml up -d --build --wait
```

重要升级前，请备份 `postgres_data` Docker Volume。

## 安全检查清单

- 生产环境使用独立的强密码。
- 不要向公网开放 `5432`、`6379` 和 `8000`。
- 输入任何敏感信息前必须启用 HTTPS。
- 匿名公开演示建议使用默认 Mock Provider。
- 接入付费 LLM 前，应增加登录鉴权与任务额度。
- 限制云防火墙规则，并及时更新 Docker 和服务器系统。
- 将任务输入和生成报告视为不可信内容处理。

## 本地开发隔离

默认开发配置将 Web、API、PostgreSQL 和 Redis 全部绑定到 `127.0.0.1`。除非主动修改 Compose 端口绑定，否则局域网中的其他设备无法连接。
