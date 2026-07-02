# 本機使用說明 / Local Usage Guide

## 繁體中文

**這是可離線在本機執行的完整版。**

1. 解壓縮後,直接**雙擊 `index.html`** 即可在瀏覽器使用(建議 Chrome/Edge/Safari)。
2. **免安裝、免網路**:比價跳板、規格相容檢查、規則式 FAQ、商業分析圖表、報價單匯出/匯入(XLS/PDF)、PPT 下載,全部離線可用(JS 套件已內含於 `libs/`)。
3. **需要網路的部分**:點出去各平台的即時搜尋、以及「真 AI」功能(FAQ 真人級客服、拍照辨識、動態商業分析)——AI 需先部署 `worker/` 內的 Cloudflare Worker 並在網站右上 ⚙️ 貼上網址(見 `worker/README.md`)。
4. **修改內容**:資料都在 `generate.py`(平台/賣家/鐵則)、`content.json`(規格庫/FAQ)、`consult.json`(顧問報告)、`research.json`(SPEC 報告/設計依據)。改完執行 `python3 generate.py` 重新產生 `index.html`。
5. 介面右上:**中/EN** 切換語言、**⚙️** 設定 AI、**🌙** 深色/護眼主題。

檔案結構:
```
index.html            主程式(產生後的成品,雙擊即用)
libs/                 本地 JS 套件(PptxGenJS、SheetJS)— 離線關鍵
assets/               賣價表圖
generate.py           產生器 + 資料(單一來源)
content.json / consult.json / research.json   內容資料(雙語)
worker/               AI 代理(選配,Cloudflare Worker)
README.md             專案總說明
```

## English

**This is the complete, offline-capable local build.**

1. Unzip, then **double-click `index.html`** to run in a browser (Chrome/Edge/Safari recommended).
2. **No install, no network needed** for: the comparison launcher, compatibility checker, rule-based FAQ, business-analysis charts, quotation export/import (XLS/PDF), and PPT download — all JS libraries are bundled in `libs/`.
3. **Network required** only for: outbound platform searches and the optional "real AI" features (AI FAQ assistant, photo recognition, dynamic business analysis) — deploy the Cloudflare Worker in `worker/` and paste its URL into ⚙️ (see `worker/README.md`).
4. **Editing content**: data lives in `generate.py` (platforms/sellers/rules), `content.json` (spec library/FAQ), `consult.json` (consultant report), `research.json` (SPEC report/design rationale). Re-run `python3 generate.py` to regenerate `index.html`.
5. Top-right controls: **中/EN** language toggle, **⚙️** AI settings, **🌙** dark/eye-care theme.
