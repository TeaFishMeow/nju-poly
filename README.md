<div align="center">

<img src="apps/web/public/brand/banner.png" alt="NJUPoly" width="880" onerror="this.style.display='none'" />

<h1>南哪竞猜 NJUPoly</h1>

<p><b>仿 Polymarket 的校内娱乐性质竞猜平台</b></p>

<p>
  南哪币 NWC · 平价彩池 · 二元竞猜 · 0 抽水 · 机器人 API
</p>

<p>
  <a href="https://github.com/TeaFishMeow/nju-poly/blob/main/LICENSE"><img src="https://img.shields.io/github/license/TeaFishMeow/nju-poly?color=f7f2e8&labelColor=2b2a26&style=flat-square" alt="License"/></a>
  <a href="https://github.com/TeaFishMeow/nju-poly/stargazers"><img src="https://img.shields.io/github/stars/TeaFishMeow/nju-poly?color=f7f2e8&labelColor=2b2a26&style=flat-square" alt="Stars"/></a>
  <a href="https://github.com/TeaFishMeow/nju-poly/network/members"><img src="https://img.shields.io/github/forks/TeaFishMeow/nju-poly?color=f7f2e8&labelColor=2b2a26&style=flat-square" alt="Forks"/></a>
  <a href="https://github.com/TeaFishMeow/nju-poly/commits/main"><img src="https://img.shields.io/github/last-commit/TeaFishMeow/nju-poly?color=f7f2e8&labelColor=2b2a26&style=flat-square" alt="Last commit"/></a>
  <a href="https://github.com/TeaFishMeow/nju-poly/pulls"><img src="https://img.shields.io/badge/PRs-welcome-f7f2e8?labelColor=2b2a26&style=flat-square" alt="PRs welcome"/></a>
</p>

<p>
  <a href="https://polymarket.exnju.top"><img src="https://img.shields.io/badge/%E2%98%81%EF%B8%8F%20%E7%AB%8B%E5%8D%B3%E4%BD%93%E9%AA%8C-f7f2e8?style=for-the-badge&labelColor=2b2a26" alt="立即体验"/></a>
  &nbsp;
  <a href="#%EF%B8%8F-快速开始"><img src="https://img.shields.io/badge/%F0%9F%8F%A0%20%E6%9C%AC%E5%9C%B0%E8%BF%90%E8%A1%8C-2b2a26?style=for-the-badge" alt="本地运行"/></a>
  &nbsp;
  <a href="https://github.com/TeaFishMeow/nju-poly"><img src="https://img.shields.io/badge/%E2%AD%90%20Star%20%E6%94%AF%E6%8C%81%E6%88%91%E4%BB%AC-2b2a26?style=for-the-badge" alt="Star"/></a>
</p>

</div>

---

## ✨ 这是什么

**南哪竞猜 NJUPoly** 是一个面向南大同学的**校内娱乐竞猜平台**，复刻 Polymarket 的简洁交易体验。

同学们用虚拟积分 **南哪币 NWC** 对校内外事件下注。平台不涉及任何现实资金：NWC 是纯 Web2 虚拟积分，由平台中心化记账，不支持外部出入金，仅在账户之间划转。

它和你见过的预测市场不同：

- 它不是博彩 —— **零现实资金**，纯积分娱乐，注册即送、签到白嫖。
- 它不是 AMM / 订单簿 —— 用最朴素的**平价彩池**，猜对的一方平分整个资金池。
- 它也开放给机器人 —— 内置有限的 **机器人 API**，供交易机器人爱好者实践。

> 「猜得开心，输赢都是积分」是 NJUPoly 想为同学们做的事。

- 🌐 站点：`https://polymarket.exnju.top`
- 💰 货币：南哪币 NWC（内部以整数「分」记账，10.00 NWC = 1000 分）

## 📸 产品速览

<!-- 把截图 / 录屏放到 docs/screenshots/ 下，文件名与下方一致即可 -->

<table>
<tr>
<td width="50%">
<img src="docs/screenshots/market-list.png" alt="竞猜首页" />
<p align="center"><sub>竞猜首页：市场卡 + 分类筛选，隐含概率实时映射成百分比</sub></p>
</td>
<td width="50%">
<img src="docs/screenshots/market-detail.png" alt="市场详情 · YES/NO 买入" />
<p align="center"><sub>市场详情：YES / NO 一键买入，概率随下注实时变化</sub></p>
</td>
</tr>
<tr>
<td width="50%">
<img src="docs/screenshots/dashboard.png" alt="个人 Dashboard" />
<p align="center"><sub>Dashboard：余额 / 持仓 / 账本 / 签到 / API Token 一站管理</sub></p>
</td>
<td width="50%">
<img src="docs/screenshots/create-event.png" alt="创建事件" />
<p align="center"><sub>创建事件：填字段 → 管理员审核 → AI 生成封面上线</sub></p>
</td>
</tr>
</table>

## 🎯 核心特性

<table>
<tr>
<td width="33%" valign="top">

#### 📈 平价彩池

YES / NO 二元市场，下注即投入资金池。隐含概率 = `yes_pool / (yes_pool + no_pool)`，随下注实时变化，0 抽水全额回流赢家。

</td>
<td width="33%" valign="top">

#### 🧾 一切皆账本

唯一资金原语 `transfer`。账本 append-only 是事实来源，余额只是缓存。整数分记账，禁浮点，杜绝精度漂移。

</td>
<td width="33%" valign="top">

#### 🎓 南大邮箱登录

仅 `学号@smail.nju.edu.cn` 邮箱验证码登录，学号即钱包地址。注册送 10.00 NWC，每日签到 +1.00。

</td>
</tr>
<tr>
<td width="33%" valign="top">

#### ⚖️ 两段式结算 + 申诉

事件状态机 `pending → open → closed → resolving → settled`。24h 申诉窗口内资金未派发，永不需要追回已派资金。

</td>
<td width="33%" valign="top">

#### 🤖 机器人 API

Dashboard 生成 / 吊销 API Token，Bearer 鉴权查市场 / 下注 / 划转 / 查余额持仓。`/docs` 即机器人文档，限流 60 次/分钟。

</td>
<td width="33%" valign="top">

#### 🌐 双语双主题

Next.js + shadcn/ui 复刻 Polymarket 简洁观感。next-intl 中英双语、next-themes 深浅色、响应式开箱即用。

</td>
</tr>
</table>

## 🚀 两种使用方式

### ☁️ 云端版 — 推荐快速体验

零配置，开箱即用。访问 **[polymarket.exnju.top](https://polymarket.exnju.top)**，用南大邮箱（`学号@smail.nju.edu.cn`）收验证码登录即可使用全部功能 —— 浏览市场、下注、创建事件、签到、生成机器人 Token。

> **适合**：想立即上手玩、不想自己跑服务的同学。

### 🏠 自托管 / 本地版

```bash
git clone https://github.com/TeaFishMeow/nju-poly.git
cd nju-poly
pnpm install
cd apps/api && uv sync && cd ../..
pnpm dev
```

打开 `http://localhost:3000` 即可。

> **适合**：二次开发者、想跑机器人 / 改规则的同学、需要数据完全本地化的场景。

## 🛠️ 快速开始

本项目**不需要 Docker**。开发和本地部署都直接在仓库目录内运行：

- JavaScript 依赖装到仓库内的 `node_modules/`，pnpm store 固定在 `.pnpm-store/`（通过 `.npmrc`）。
- Python 依赖由 `uv` 装到 `apps/api/.venv/`。
- SQLite 数据库、媒体文件等本地运行数据放在 `apps/api/.local/`。

### 环境要求

本机只需具备入口命令：**Node.js · pnpm · Python · uv**。

### 安装与启动

```bash
# 安装依赖
pnpm install
cd apps/api && uv sync && cd ../..

# 从仓库根目录启动 web + api
pnpm dev
```

| 服务 | 地址 |
| --- | --- |
| Web | `http://localhost:3000` |
| API | `http://127.0.0.1:8000` |
| OpenAPI docs | `http://127.0.0.1:8000/docs` |

API 起来后生成共享 TS 客户端：

```bash
pnpm codegen
```

本地配置写在 `.env`（见 `.env.example`）。SMTP 口令、图片模型 key 等密钥**必须留在 Git 之外**。

## 🧱 技术栈

| 类别 | 选型 |
|---|---|
| 前端框架 | **Next.js** (App Router) + **TypeScript** |
| 样式 / 组件 | **TailwindCSS** · **shadcn/ui** |
| 国际化 / 主题 | **next-intl** · **next-themes** |
| 后端框架 | **FastAPI** + **Pydantic v2** |
| ORM / 迁移 | **SQLAlchemy 2.0** · **Alembic** |
| 数据库 | 本地 **SQLite** / 生产 **PostgreSQL** |
| 鉴权 | **Bearer Token**（前端与机器人同一套） |
| 类型契约 | **OpenAPI** → `openapi-typescript` 生成 TS 客户端 |
| 图片生成 | **gpt-image-2**（OpenAI 兼容接口） |
| 包管理 | **pnpm workspace**（JS）· **uv**（Python） |

仓库为 Monorepo：

```text
apps/web        Next.js 前端
apps/api        FastAPI 后端（uv 管理依赖）
packages/shared OpenAPI 生成的 TS 客户端与共享类型
```

## 🧠 架构要点

整个平台只有一个资金原语：**转账**。

```text
transfer(from, to, amount, kind, ref)

注册赠币   system     → u:<学号>
每日签到   system     → u:<学号>
下注       u:<学号>   → event:<id>
派彩       event:<id> → u:<学号>
点对点划转 u:<学号>   → u:<学号>
```

- **一切皆账本转账**：账户是字符串键（用户 `u:<学号>`、系统 `system`、资金池 `event:<id>`）。资金池就是一个普通账户，没有「加余额 / 减余额」的分支。
- **账本 append-only**：`ledger` 表只增不改，是资金事实来源；`accounts.balance` 是同事务内原子更新的去规范化缓存。
- **整数分记账**：内部一律 `BIGINT` 存分，禁止浮点，前端展示再 `/100`。
- **结算算法**：设结果为 YES、`pot` 为资金池、`W` 为获胜方总下注，每个赢家 i 得 `pot × stake_i / W`；无人押中则全额退款。取整用最大余数法，结算后资金池恰好归零。

设计准则贯穿全程：**无特判、无兜底 / 回退、强解耦、忽略迁移兼容**。能跑即成功，跑不动即报错。

## 📜 核心规则

| 维度 | 规则 |
| --- | --- |
| 注册门槛 | 仅 `学号@smail.nju.edu.cn`，邮箱验证码登录，学号即钱包地址 |
| 新用户赠币 | 注册即获 10.00 NWC |
| 每日签到 | 每日签到获 1.00 NWC（`Asia/Shanghai` 自然日，重复签到报错） |
| 市场类型 | 仅 YES / NO 二元市场，不做多选 |
| 下注 | 最小 0.01 NWC；不可撤单、不可卖出；可同时双押 YES 与 NO |
| 抽水 | 0 手续费，资金池全额回流赢家 |
| 申诉 | 仅事件参与者，在 24h 固定窗口内可申诉 |
| 机器人 API | 每 Token 60 次/分钟，无下注上限 |

## 🤖 机器人 API

机器人接入在 Dashboard 管理：在那里生成 API Token，然后带 `Authorization: Bearer <token>` 调用 `/robot/*` 端点。机器人 API 支持市场读取、下注、查余额、查持仓、点对点划转，每 Token 限流 60 次/分钟。`/docs` 即机器人 API 参考。

## 🎨 图片资产

Logo 与事件封面由图片模型生成：

```bash
pnpm generate-art   # 生成
pnpm verify-art     # 校验为模型产物而非本地 SVG 回退
```

需要 `.env` 中的 `IMAGE_MODEL_API_KEY`。事件封面存于 `apps/api/.local/media/` 并写回本地 SQLite，DB 只存 URL；选定的 Logo 存于 `apps/web/public/brand/`。

## ☁️ 生产部署

前端走 Vercel，后端是云服务器上直接运行的 FastAPI 进程（无 Docker）。

| 入口 | 地址 |
| --- | --- |
| Web | `https://polymarket.exnju.top` |
| 浏览器侧 API | `https://polymarket.exnju.top/api` |

DNS 与 TLS 就绪后运行线上冒烟检查：

```bash
pnpm smoke:prod
```

## 🗺️ Roadmap

- [ ] 🎴 抽卡页：用 NWC 抽取数字资产
- [ ] 💬 论坛与事件评论区
- [ ] 📊 概率走势图（历史隐含概率可视化）
- [ ] 🤝 点对点划转体验优化
- [ ] 🤖 官方机器人 SDK 与示例脚本
- [ ] 📱 移动端体验深度优化
- [ ] 🌍 更多语言

## 🤝 贡献

欢迎任何形式的贡献 —— Issue、PR、文档改进、设计建议、使用反馈。

- 🐛 反馈问题：[新建 Issue](https://github.com/TeaFishMeow/nju-poly/issues/new)
- 💡 提议特性：[GitHub Discussions](https://github.com/TeaFishMeow/nju-poly/discussions)
- 🔧 提交代码：Fork → 改动 → Pull Request

### 贡献者

<a href="https://github.com/TeaFishMeow/nju-poly/graphs/contributors">
  <img src="https://contrib.rocks/image?repo=TeaFishMeow/nju-poly" alt="Contributors" />
</a>

## 💬 社区

- 💬 **GitHub Discussions**: [加入讨论](https://github.com/TeaFishMeow/nju-poly/discussions)
- 🐛 **Issue 反馈**: [github.com/TeaFishMeow/nju-poly/issues](https://github.com/TeaFishMeow/nju-poly/issues)

## 📄 许可证

本项目为校内娱乐性质原型。许可证详见仓库 [LICENSE](./LICENSE)。

---

<div align="center">
<sub>Made with ☕ at NJU · 猜得开心，输赢都是积分。</sub><br/>
<sub>如果 NJUPoly 让你猜得开心 —— 请给我们一颗 ⭐</sub>
</div>
