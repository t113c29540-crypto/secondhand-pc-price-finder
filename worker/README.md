# AI 代理 (Cloudflare Worker)

把靜態網站的「規則式 FAQ」與「手動拍照」升級成**真 AI**。金鑰只存在 Worker 的密鑰環境變數,**前端永遠看不到金鑰**(GitHub Pages 是公開的,金鑰絕不能放前端)。

沒有部署這個 Worker,網站照常運作(自動退回規則式 FAQ + 手動型號)。部署並在網站 ⚙️ 設定貼上 Worker 網址後,就變真 AI。

## 部署步驟

1. 安裝 Node 後,在 `worker/` 目錄登入 Cloudflare:
   ```bash
   cd worker
   npx wrangler login
   ```
2. 設定金鑰(二選一,依 `wrangler.toml` 的 `PROVIDER`):
   ```bash
   npx wrangler secret put ANTHROPIC_API_KEY   # 用 Claude(預設)
   # 或
   npx wrangler secret put OPENAI_API_KEY       # 若把 PROVIDER 改成 openai
   ```
   - Claude 金鑰:<https://console.anthropic.com/> → API Keys
   - OpenAI 金鑰:<https://platform.openai.com/api-keys>
3. (建議)把 `wrangler.toml` 的 `ALLOWED_ORIGIN` 改成你的 Pages 網址,鎖定來源。
4. 部署:
   ```bash
   npx wrangler deploy
   ```
   會得到一個網址,例如 `https://pcfinder-ai-proxy.<你的帳號>.workers.dev`。
5. 打開網站 → 右上 **⚙️** → 貼上這個 Worker 網址 → 儲存。FAQ 客服與拍照辨識就變真 AI 了。

## 模型與費用
- 預設 `MODEL = claude-opus-4-8`(最聰明)。**省錢**可在 `wrangler.toml` 改成 `claude-haiku-4-5`(便宜)或 `claude-sonnet-4-6`,再 `npx wrangler deploy`。
- 用 OpenAI:把 `PROVIDER` 改 `openai`、`MODEL` 改 `gpt-4o-mini`,並改設 `OPENAI_API_KEY`。
- 這支 Worker 免費額度通常夠個人用;費用主要是你自己的 API 用量,由你的金鑰計費。

## 三個模式(前端會自動呼叫)
| mode | 用途 |
|---|---|
| `chat` | FAQ 客服真 AI 問答(繁中、防詐、相容性) |
| `vision` | 拍照/上傳 → 辨識零件型號與規格(回 JSON) |
| `analysis` | 輸入任意標的 → 產生五力/BMC/SWOT(供動態商業分析 + 下載 PPT) |

## 會員審核(只開放審核通過的會員用 AI)
- 在 Worker 變數加 **`MEMBER_CODES`**(Text 明文即可),值為逗號分隔的會員碼名單,例:`BRO-2026,MOM-01,GUEST-7`。
- **設定後**:所有 AI 模式(chat/vision/analysis)都要求有效會員碼;沒碼或碼錯回 `401 member_required`,網站會自動退回免費的規則式 FAQ。
- **留空或不設** = 不啟用審核(所有人可用)。
- **核發會員**:把新碼加進名單 → Deploy;**撤銷**:從名單移除 → Deploy。建議一人一碼,方便單獨撤銷。
- 會員在網站右上 **⚙️ → 會員碼** 欄輸入,存在他自己的瀏覽器(localStorage),之後自動帶上。

## 安全
- 金鑰用 `wrangler secret` 存,不要寫進 `wrangler.toml` 或前端。
- 建議把 `ALLOWED_ORIGIN` 鎖成你的 Pages 網址,避免被別人盜用你的額度。
- `MEMBER_CODES` 是第二道防線:就算有人拿到 Worker 網址,沒有會員碼也用不了你的額度。
