# 🖥️ 二手電腦詢價系統 (Second-hand PC Price Finder)

輸入型號或品名（例：`i7-6700`、`H110M-K D3`、`MacBook Pro`），**一鍵跳到全球前 10 大二手／整新平台的真實搜尋結果**比價。專為台灣使用者買二手電腦／零件設計，內建防詐下單鐵則、詢價範本與信任賣家直達。

> 🔗 線上版：**https://t113c29540-crypto.github.io/secondhand-pc-price-finder/**

## ✨ 特色

- **一鍵詢價**：輸入關鍵字，同時開啟 10 個平台的搜尋結果（露天、Yahoo拍賣、蝦皮、旋轉拍賣、FB Marketplace、eBay、Back Market、Swappa、Amazon Renewed、Mercari 日本）。
- **台灣／國際篩選**：分開台灣平台與國際整新機平台。
- **誠實比價**：只開啟各平台的**真實搜尋**，不爬價、不造假快取價，價格以平台即時頁面為準。
- **防詐內建**：7 條下單鐵則 + 可一鍵複製的詢價範本，避免「標錯價反悔」「下單才改價」。
- **信任賣家直達**：露天實查彙整的高評價賣家（如桀鑫電腦、JULE 3C會社、知飾家等）。
- **純靜態**：免後端、免資料庫，直接放上 GitHub Pages。手機／桌面皆響應式。

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

## 📦 部署到 GitHub Pages

本專案是純靜態網站，`index.html` 在根目錄即可。

1. 推上 GitHub。
2. Repo → **Settings → Pages → Build and deployment → Source 選 "Deploy from a branch"**，Branch 選 `main` / `/ (root)`，存檔。
3. 約 1 分鐘後即可由 `https://<帳號>.github.io/<repo>/` 開啟。

## ⚠️ 免責聲明

本工具僅整理「搜尋入口」與一般防詐建議，**不販售商品、不保證任何賣家或價格**。實際交易請自行判斷賣家信用，建議一律**貨到付款、收到先驗、不對拒收**。

---
🤖 以 [Claude Code](https://claude.com/claude-code) 製作
