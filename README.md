# 南哪竞猜 NJUPoly

NJUPoly is a campus entertainment prediction-market prototype inspired by Polymarket.

## 本地目录部署

本项目不需要 Docker，也不需要 docker compose。开发和本地部署都直接在
当前仓库目录内运行：

- JavaScript 依赖安装到仓库内的 `node_modules/`，pnpm store 固定在
  `.pnpm-store/`。
- Python 依赖由 `uv` 安装到 `apps/api/.venv/`。
- SQLite 数据库、媒体文件等本地运行数据放在 `apps/api/.local/`。

本机只需要具备这些入口命令：

- Node.js
- pnpm
- Python
- uv

安装项目内依赖：

```bash
pnpm install
cd apps/api
uv sync
cd ../..
```

从仓库根目录启动本地服务：

```bash
pnpm dev
```

这会直接从当前目录启动 API 和 Web。默认本地数据库是
`apps/api/.local/` 下的 SQLite 文件。

- API: `http://127.0.0.1:8000`
- Web: `http://localhost:3000`
- OpenAPI docs: `http://127.0.0.1:8000/docs`

Generate the shared TypeScript OpenAPI client after the API is running:

```bash
pnpm codegen
```

Robot API access is managed from Dashboard. Generate an API Token there, then
call `/robot/*` endpoints with `Authorization: Bearer <token>`. The robot API
supports market reads, bets, account balance, positions, and P2P transfers, with
a per-token limit of 60 requests per minute. `/docs` is the robot API reference.

Generate the Logo and event cover art with the image model from `ai.md`:

```bash
pnpm generate-art
pnpm verify-art
```

This requires `IMAGE_MODEL_API_KEY` in `.env`. Generated event covers are saved
under `apps/api/.local/media/` and written back to the local SQLite database;
the selected Logo is saved under `apps/web/public/brand/`. `pnpm verify-art`
checks that the selected Logo and all non-rejected event covers are raster
model outputs rather than local SVG fallbacks.

Local configuration lives in `.env`. Secrets such as SMTP credentials and
image-model keys must stay out of Git.

The project pins pnpm's store to `.pnpm-store/` through `.npmrc`, so JavaScript
package data stays inside this workspace.

## Production deployment

Production deployment is documented in `DEPLOYMENT.md`. Goal 12 uses Vercel for
the web app and a direct, no-Docker FastAPI process on the API server:

- Web: `https://polymarket.exnju.top`
- API: `https://api.polymarket.exnju.top`

Run the production smoke check after DNS and TLS are live:

```bash
pnpm smoke:prod
```
