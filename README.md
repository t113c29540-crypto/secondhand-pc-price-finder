# 🖥️ 二手電腦詢價系統 (Second-hand PC Price Finder)

輸入型號或品名（例：`i7-6700`、`H110M-K D3`、`MacBook Pro`），**一鍵跳到全球前 10 大二手／整新平台的真實搜尋結果**比價。專為台灣使用者買二手電腦／零件設計，內建防詐下單鐵則、詢價範本與信任賣家直達。

> 🔗 線上版：**https://t113c29540-crypto.github.io/secondhand-pc-price-finder/**

## 📦 本機完整包(離線可用)

**[⬇️ 下載 pcfinder_完整包_v6.zip](https://github.com/t113c29540-crypto/secondhand-pc-price-finder/raw/main/release/pcfinder_完整包_v6.zip)** — 解壓後雙擊 `index.html` 即用;JS 套件已本地化(`libs/`),離線可跑。詳見 [README_本機使用_LOCAL.md](README_本機使用_LOCAL.md)。

## ✨ 特色（v6）

**v6 新增**:**每日動態更新**(站內每日提示/精選輪播＋GitHub Actions 每日 05:00 自動重建);**🎬 動態簡報**(7 頁自動播放/鍵盤/進度點:封面示意圖→市場→SPEC→**五維雷達比較**→價格→優缺點→行動);雷達 3 系列色盤通過 CVD/對比驗證;SPEC 表每列 **📷 官網圖**連結(原廠產品頁真照片,已逐一驗證可達;基於版權不內嵌);UI 打磨(focus ring、44px 觸控目標、手機置底比價鈕)。

**v5 新增**:護眼配色(WCAG AA 對比、低藍光暖色系)、全站字級加大、**動態流程圖/圖表**(節點浮現+箭頭描邊+長條生長動畫,含重播鈕、respect `prefers-reduced-motion`)、**SWOT 縮放**(50–150%)、**🧾 SPEC 報價分頁**(各廠商主機板/CPU/相關產品完整規格與優缺點、CP 值公式、編號參考文獻 [1]–[13])、**報價單匯出/匯入**(真 .xlsx 回圈編輯 + PDF 列印)、**設計依據**(實查世界前 10 大二手網站的可落地設計模式,文獻 [10]–[20])、JS 套件本地化(離線)、ELI20 與使用指南全文精修(雙語)。

六大分頁，全部純靜態、手機／桌面響應式、支援深色模式：

1. **🔎 詢價比價**：輸入關鍵字，一鍵全開 10 大平台真實搜尋（露天、Yahoo拍賣、蝦皮、旋轉、FB、eBay、Back Market、Swappa、Amazon Renewed、Mercari 日本）。含常買零件快速分類、**載入 LINE 對話 txt 自動抓型號**、一鍵比價書籤。
2. **✅ 精選賣家**：露天實查高評價賣家直達 + 兩張賣價對照表（PNG）。
3. **🧩 規格相容**：選 CPU＋主機板＋記憶體 → **自動判斷相容性**（腳位／晶片組世代／DDR3-D3 vs DDR4）；可勾選零件產生**規格比較表**；附零件規格庫與相容規則。
4. **📷 拍照找件**：開相機／上傳照片 → 輸入型號自動查相容＋比價 → Google Lens 以圖搜尋。**設定 AI 後可「🤖 AI 辨識照片」** 直接讀型號與規格（Claude/OpenAI 視覺）。
5. **📊 商業分析**：**波特五力雷達圖、商業模式圖 BMC、SWOT**（SVG，跟隨深色模式）。可**輸入任意標的動態產生**（需 AI）、並**一鍵下載 PPT**（PptxGenJS，純前端，4 頁：封面＋五力＋BMC＋SWOT）。
6. **💬 FAQ 客服**：**未設定 AI** 用知識庫**規則式問答**（15 題）；**設定 AI 後**升級成**真 AI 客服**（繁中、防詐、相容性；連線失敗自動退回規則式）。
7. **📑 顧問報告（雙語）**：以顧問角度、**參考國際期刊／產業報告／企業公開資訊**（9 筆可查證來源）做的報告 — 使用指南、**運作流程圖（SVG，圖文分開、大字）**、市場與文獻、**誠實紅隊評估**（truthmode/redteam/blindspot，不吹捧）、ELI15 白話+範例、**變現·定價·行動計畫**。右上 **中/EN** 一鍵切換繁中↔英文（導覽列與報告內容全雙語）。

**誠實原則**：只開各平台真實搜尋，不爬價、不造假快取價；「AI 自動辨識／真 AI 客服」需 API 後端，靜態站以可行的誠實版替代並標明升級路徑。

## 🗂️ 資料來源
- `generate.py`：平台、分類、信任賣家、防詐鐵則、詢價範本、快速關鍵字（最上方常數）。
- `content.json`：零件規格庫、FAQ 知識庫、五力／BMC／SWOT 內容（多代理研究產出，可手改）。
- `assets/`：兩張賣價表 PNG。
- `consult.json`：顧問報告內容（市場文獻、紅隊評估、變現、使用指南、流程圖節點，皆雙語 zh/en；多代理研究產出，可手改）。
- `research.json`：v5 研究資料（世界前 10 大二手網站設計模式、各廠商 SPEC 比價報告＋公式＋編號文獻、ELI20 精修文字，皆雙語）。
- `libs/`：本地化 JS 套件（PptxGenJS、SheetJS）— 離線可用的關鍵。
- `release/`：本機完整包 zip。

## 🚀 本機使用

```bash
# 1) 由 Python 產生 index.html（資料來源是 generate.py）
python3 generate.py

# 2) 本機預覽
python3 -m http.server 8000
# 瀏覽器開 http://localhost:8000
```

### 終端機詢價（不開瀏覽器也能用）

```bash
python3 generate.py search "i7-6700 主機板"
# 會列出 10 個平台的詢價直達連結
```

## 🛠️ 更新資料

所有資料（平台清單、信任賣家、防詐鐵則、詢價範本、快速關鍵字）都在 **`generate.py`** 最上方的常數區。
改完後重跑 `python3 generate.py` 即可重新產生 `index.html`，再 push 上去就更新了。

| 想改什麼 | 改哪裡 |
|---|---|
| 平台清單／搜尋網址 | `PLATFORMS` |
| 信任賣家 | `TRUSTED_SELLERS` |
| 防詐鐵則 | `RULES` |
| 詢價範本 | `INQUIRY_TEMPLATE` |
| 快速關鍵字 | `QUICK_KEYWORDS` |
| 常買零件分類 | `CATEGORIES` |
| 零件規格庫／相容規則 | `content.json` → `parts` |
| FAQ 知識庫 | `content.json` → `faq` |
| 五力／BMC／SWOT | `content.json` → `fiveForces`／`bmc`／`swot` |

## 🤖 真 AI 升級（選配）

GitHub Pages 是純靜態、**不能放 API 金鑰**（會被盜刷）。要把 FAQ 客服與拍照辨識變「真 AI」、並動態產生商業分析，部署一個 **Cloudflare Worker 代理**（金鑰只存在 Worker 的密鑰環境變數）即可；前端在 ⚙️ 貼上 Worker 網址就升級，**沒部署也能用**（自動退回規則式／手動）。

- 步驟：[`worker/README.md`](worker/README.md)
- 支援 **Claude（預設 `claude-opus-4-8`）或 OpenAI**；可換模型省錢（`claude-haiku-4-5` 等）。
- 三模式：`chat`（FAQ 客服）、`vision`（拍照辨識零件）、`analysis`（動態五力/BMC/SWOT）。

## 📦 部署到 GitHub Pages

本專案是純靜態網站，`index.html` 在根目錄即可。

1. 推上 GitHub。
2. Repo → **Settings → Pages → Build and deployment → Source 選 "Deploy from a branch"**，Branch 選 `main` / `/ (root)`，存檔。
3. 約 1 分鐘後即可由 `https://<帳號>.github.io/<repo>/` 開啟。

## ⚠️ 免責聲明

本工具僅整理「搜尋入口」與一般防詐建議，**不販售商品、不保證任何賣家或價格**。實際交易請自行判斷賣家信用，建議一律**貨到付款、收到先驗、不對拒收**。

---
🤖 以 [Claude Code](https://claude.com/claude-code) 製作
