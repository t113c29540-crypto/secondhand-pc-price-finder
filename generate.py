#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
二手電腦詢價系統 — 產生器 (Python -> 靜態 HTML)
=================================================
這支程式是「資料的單一來源」。改下面的 PLATFORMS / TRUSTED_SELLERS / RULES
後重跑，就會重新產生 index.html（可直接放上 GitHub Pages）。

用法：
    python3 generate.py                 # 產生 index.html
    python3 generate.py search "i7-6700"  # 在終端機列出各平台的詢價直達連結

作者面向：台灣使用者，買二手電腦／零件（主機板、CPU、記憶體、筆電、整機）。
設計原則：不爬價、不造假。一鍵開啟各平台的「真實搜尋結果」比價，價格以平台即時頁面為準。
"""

import json
import sys
import datetime
from urllib.parse import quote

# ─────────────────────────────────────────────────────────────────────────────
# 全球前 10 大二手電腦交易平台（台灣優先，國際整新機為輔）
# url 內的 {q} 會被搜尋關鍵字取代（前端會自動做 URL 編碼）
# ─────────────────────────────────────────────────────────────────────────────
PLATFORMS = [
    {
        "rank": 1, "name": "露天市集 Ruten", "emoji": "🛒", "region": "tw",
        "type": "C2C 拍賣／賣場",
        "url": "https://www.ruten.com.tw/find/?q={q}",
        "good": "台灣最大拍賣，二手零件、板U套最齊全",
        "risk": "賣家良莠不齊，慎防標錯價／陸貨拆機，認評價數",
    },
    {
        "rank": 2, "name": "Yahoo奇摩拍賣", "emoji": "🟣", "region": "tw",
        "type": "C2C 拍賣",
        "url": "https://tw.bid.yahoo.com/search/auction/product?p={q}",
        "good": "台灣老牌拍賣，個人出清二手多",
        "risk": "介面較舊，賣家數比露天少",
    },
    {
        "rank": 3, "name": "蝦皮購物 Shopee", "emoji": "🦐", "region": "tw",
        "type": "電商／賣場",
        "url": "https://shopee.tw/search?keyword={q}",
        "good": "量大、折價券多、店到店便宜",
        "risk": "大量中國跨境拆機／充新，認『台灣現貨/出貨地』",
    },
    {
        "rank": 4, "name": "旋轉拍賣 Carousell", "emoji": "🔄", "region": "tw",
        "type": "C2C 二手",
        "url": "https://www.carousell.com.tw/search/{q}",
        "good": "台灣在地個人二手出清，可議價、可面交",
        "risk": "無平台金流保障時，盡量面交驗機",
    },
    {
        "rank": 5, "name": "Facebook Marketplace／社團", "emoji": "📘", "region": "tw",
        "type": "C2C 在地面交",
        "url": "https://www.facebook.com/marketplace/search/?query={q}",
        "good": "在地面交、可當場驗機開機點亮最安心",
        "risk": "私下交易無保障，只約公開場所、不先匯款",
    },
    {
        "rank": 6, "name": "eBay", "emoji": "🌐", "region": "intl",
        "type": "國際拍賣／二手",
        "url": "https://www.ebay.com/sch/i.html?_nkw={q}",
        "good": "全球最大二手／整新市場，買家保護完整",
        "risk": "國際運費＋關稅，到貨慢，注意可否寄台灣",
    },
    {
        "rank": 7, "name": "Back Market", "emoji": "♻️", "region": "intl",
        "type": "專業整新機 (Refurbished)",
        "url": "https://www.backmarket.com/en-us/search?q={q}",
        "good": "歐美專業整新機平台，分級清楚、附保固",
        "risk": "以筆電／手機為主，零件少；需國際運送",
    },
    {
        "rank": 8, "name": "Swappa", "emoji": "🤝", "region": "intl",
        "type": "二手 3C（美國）",
        "url": "https://swappa.com/search?q={q}",
        "good": "美國二手 3C，上架前審核、買家保障佳",
        "risk": "以筆電／手機／平板為主，主要寄美國境內",
    },
    {
        "rank": 9, "name": "Amazon Renewed", "emoji": "📦", "region": "intl",
        "type": "官方整新機",
        "url": "https://www.amazon.com/s?k={q}+renewed",
        "good": "Amazon 認證整新，附 Renewed 保固",
        "risk": "並非所有品項寄台灣，注意運送與保固範圍",
    },
    {
        "rank": 10, "name": "Mercari 日本", "emoji": "🇯🇵", "region": "intl",
        "type": "C2C 二手（日本）",
        "url": "https://jp.mercari.com/search?keyword={q}",
        "good": "日本二手『美品』多、成色好",
        "risk": "需日本集運轉送，溝通／運費成本較高",
    },
]

# 對照避雷（不放進前 10，但提醒）
AVOID = "🇨🇳 閒魚／AliExpress 等中國平台、以及 X79/X99+Xeon E5『洋垃圾』伺服器板：便宜但無台灣保固、耗電、品質參差，文書看影片用不到，避開。"

# ─────────────────────────────────────────────────────────────────────────────
# 信任賣家直達（露天，依本專案實查評價彙整，2026/6）
# ─────────────────────────────────────────────────────────────────────────────
TRUSTED_SELLERS = [
    {"name": "桀鑫電腦", "account": "js3c0800",
     "note": "華碩 H110M-K D3 等 DDR3 板，評價約 2.1 萬、價格最低"},
    {"name": "JULE 3C會社", "account": "jule1087",
     "note": "華碩 H110M-C/A/E D3 款式齊、標良品，評價約 1.2 萬"},
    {"name": "知飾家", "account": "ymy65668",
     "note": "少數主打『真二手良品』台灣賣家，評價約 3,867"},
    {"name": "小圓二手拍賣", "account": "jacky0930",
     "note": "台廠華碩真二手板U，可沿用 i7-6700，評價約 3,080"},
    {"name": "光代電子", "account": "el_zerg",
     "note": "板U大賣場、含發票，評價全場最高（約 9,239）"},
]

# ─────────────────────────────────────────────────────────────────────────────
# 防詐下單鐵則
# ─────────────────────────────────────────────────────────────────────────────
RULES = [
    "一律「貨到付款」，收到先驗：開機點亮、CPU-Z 認型號，不對就<b>拒收</b>。",
    "認規格別只看標題：<b>LGA 腳位、DDR3／DDR4、D3／D4 版本</b>要對得上你的零件。",
    "下單前請賣家<b>白紙黑字確認「頁面價＝成交價」</b>，防『標錯價』事後反悔。",
    "先<b>確認現貨</b>，擋掉「下單後才說缺貨／改價」這招。",
    "簡體文案（主板／內存／臺式）＋淘寶圖＋引導加 LINE ＝ 中國跨境貨，留意保固。",
    "<b>評價數多、好評率 99%＋、開店久</b>優先；同型號多比 2–3 家，別只看最低價。",
    "貨到付款沒付錢前你<b>零風險</b>；賣家不出貨會被記『賣家未出貨』，責任在他。",
]

# 詢價範本（可一鍵複製）
INQUIRY_TEMPLATE = """您好，想跟您確認這件商品，確認後馬上下單：
1. 規格是否正確？（腳位／記憶體版本／型號，例：LGA1151 + DDR3L，不是 DDR4）
2. 目前有現貨嗎？全新還是二手拆機？二手有測試過、正常開機點亮嗎？
3. 頁面標的價格就是最終成交價嗎？含運、貨到付款一共多少？
4. 有保固／七天測試良品嗎？收到不能用可否退換？
麻煩確認後再請您保留現貨，謝謝！"""

# 快速關鍵字（一鍵帶入）
QUICK_KEYWORDS = [
    "i7-6700", "H110M-K D3 主機板", "DDR4 8G 記憶體", "i5-9400F",
    "RTX 3060", "MacBook Pro 二手", "二手主機 文書",
]


def build_html() -> str:
    today = datetime.date.today().isoformat()
    app_data = {
        "platforms": PLATFORMS,
        "trusted": TRUSTED_SELLERS,
        "rules": RULES,
        "template": INQUIRY_TEMPLATE,
        "quick": QUICK_KEYWORDS,
        "avoid": AVOID,
        "date": today,
    }
    data_json = json.dumps(app_data, ensure_ascii=False)
    return HTML_TEMPLATE.replace("/*__APP_DATA__*/", data_json)


def cli_search(keyword: str) -> None:
    print(f"\n🔎 「{keyword}」各平台詢價直達：\n")
    for p in PLATFORMS:
        url = p["url"].replace("{q}", quote(keyword))
        print(f"  {p['rank']:>2}. {p['name']}\n      {url}\n")
    print("提醒：價格以各平台即時頁面為準；一律貨到付款、收到先驗、不對拒收。\n")


HTML_TEMPLATE = r"""<!DOCTYPE html>
<html lang="zh-Hant">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>二手電腦詢價系統｜全球前 10 大平台一鍵比價</title>
<meta name="description" content="台灣二手電腦詢價系統：輸入關鍵字一鍵跳到全球前 10 大二手／整新平台的真實搜尋結果，內建防詐下單鐵則、詢價範本與信任賣家直達。">
<style>
  :root{
    --bg:#f4f6fb; --card:#ffffff; --ink:#1f2430; --sub:#6b7280; --line:#e6e9f0;
    --accent:#2f5496; --accent2:#3b82f6; --tw:#16a34a; --intl:#7c3aed;
    --warn:#b91c1c; --chip:#eef2fb; --shadow:0 1px 3px rgba(16,24,40,.08),0 1px 2px rgba(16,24,40,.06);
  }
  *{box-sizing:border-box}
  body{margin:0;background:var(--bg);color:var(--ink);
    font-family:-apple-system,"PingFang TC","Microsoft JhengHei",system-ui,"Segoe UI",sans-serif;
    line-height:1.6;-webkit-text-size-adjust:100%}
  .wrap{max-width:1040px;margin:0 auto;padding:18px 16px 60px}
  header{text-align:center;padding:14px 0 6px}
  h1{font-size:1.55rem;margin:.2rem 0;letter-spacing:.5px}
  .tagline{color:var(--sub);font-size:.92rem;margin:0 0 4px}
  /* search */
  .searchbox{position:sticky;top:0;z-index:20;background:var(--bg);padding:12px 0 8px;margin-top:8px}
  .searchrow{display:flex;gap:8px}
  #kw{flex:1;font-size:1.05rem;padding:13px 14px;border:1.5px solid var(--line);border-radius:12px;
    background:var(--card);box-shadow:var(--shadow);outline:none}
  #kw:focus{border-color:var(--accent2)}
  .btn{border:0;border-radius:12px;padding:0 16px;font-size:1rem;font-weight:700;cursor:pointer;
    background:var(--accent);color:#fff;white-space:nowrap}
  .btn:active{transform:translateY(1px)}
  .chips{display:flex;flex-wrap:wrap;gap:7px;margin-top:9px}
  .chip{background:var(--chip);border:1px solid var(--line);color:var(--accent);
    padding:5px 11px;border-radius:999px;font-size:.85rem;cursor:pointer}
  .chip:hover{background:#e2e8fb}
  .filters{display:flex;gap:7px;margin:10px 0 2px}
  .filt{flex:1;text-align:center;padding:8px;border:1px solid var(--line);border-radius:10px;
    background:var(--card);cursor:pointer;font-weight:600;font-size:.9rem;color:var(--sub)}
  .filt.on{background:var(--accent);color:#fff;border-color:var(--accent)}
  /* section */
  h2{font-size:1.1rem;margin:26px 0 10px;display:flex;align-items:center;gap:8px}
  .grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(252px,1fr));gap:12px}
  .pcard{background:var(--card);border:1px solid var(--line);border-radius:14px;padding:13px 14px;
    box-shadow:var(--shadow);display:flex;flex-direction:column;gap:6px}
  .ptop{display:flex;align-items:center;gap:9px}
  .rankb{background:var(--accent);color:#fff;font-weight:800;font-size:.8rem;min-width:26px;height:26px;
    border-radius:8px;display:flex;align-items:center;justify-content:center}
  .pname{font-weight:700;font-size:1rem;line-height:1.25}
  .ptags{display:flex;flex-wrap:wrap;gap:5px;margin:2px 0}
  .tag{font-size:.72rem;padding:2px 8px;border-radius:999px;font-weight:600}
  .tag.tw{background:#dcfce7;color:var(--tw)}
  .tag.intl{background:#ede9fe;color:var(--intl)}
  .tag.type{background:#eef2fb;color:var(--accent)}
  .pgood{font-size:.86rem;color:var(--ink)}
  .prisk{font-size:.8rem;color:var(--warn)}
  .pgo{margin-top:6px;text-align:center;text-decoration:none;font-weight:700;font-size:.95rem;
    background:var(--accent2);color:#fff;padding:9px;border-radius:10px;display:block}
  .pgo:active{transform:translateY(1px)}
  .pgo.disabled{background:#cbd5e1;pointer-events:none}
  /* sellers */
  .scard{background:var(--card);border:1px solid var(--line);border-radius:12px;padding:11px 13px;
    box-shadow:var(--shadow);display:flex;justify-content:space-between;align-items:center;gap:10px;margin-bottom:9px}
  .sname{font-weight:700}.sacct{color:var(--sub);font-size:.8rem}
  .snote{font-size:.84rem;color:var(--sub)}
  .sgo{text-decoration:none;background:var(--tw);color:#fff;font-weight:700;padding:8px 13px;border-radius:9px;white-space:nowrap;font-size:.88rem}
  /* rules + template */
  .panel{background:var(--card);border:1px solid var(--line);border-radius:14px;padding:15px 17px;box-shadow:var(--shadow)}
  .panel ol{margin:0;padding-left:1.25rem}.panel li{margin:6px 0;font-size:.92rem}
  .tpl{position:relative}
  pre{white-space:pre-wrap;background:#0f172a;color:#e2e8f0;border-radius:12px;padding:14px 14px 14px;
    font-size:.86rem;line-height:1.7;margin:0;font-family:inherit}
  .copy{position:absolute;top:10px;right:10px;background:#334155;color:#fff;border:0;border-radius:8px;
    padding:6px 11px;font-size:.8rem;cursor:pointer;font-weight:700}
  .copy.done{background:var(--tw)}
  .avoid{margin-top:10px;background:#fef2f2;border:1px solid #fecaca;color:#7f1d1d;border-radius:12px;
    padding:11px 14px;font-size:.86rem}
  footer{margin-top:34px;text-align:center;color:var(--sub);font-size:.8rem;line-height:1.7}
  a.src{color:var(--accent)}
  @media(max-width:520px){h1{font-size:1.3rem}.searchrow .btn{padding:0 13px}}
</style>
</head>
<body>
<div class="wrap">
  <header>
    <h1>🖥️ 二手電腦詢價系統</h1>
    <p class="tagline">輸入關鍵字，一鍵跳到全球前 10 大二手／整新平台的真實搜尋結果比價</p>
  </header>

  <div class="searchbox">
    <div class="searchrow">
      <input id="kw" type="search" placeholder="輸入型號或品名，例：i7-6700、H110M-K D3、MacBook Pro" autocomplete="off">
      <button class="btn" id="goAll">一鍵詢價</button>
    </div>
    <div class="chips" id="chips"></div>
    <div class="filters">
      <div class="filt on" data-region="all">全部</div>
      <div class="filt" data-region="tw">🇹🇼 台灣平台</div>
      <div class="filt" data-region="intl">🌐 國際／整新</div>
    </div>
  </div>

  <h2>🏆 全球前 10 大二手電腦平台</h2>
  <div class="grid" id="platforms"></div>
  <div class="avoid" id="avoid"></div>

  <h2>✅ 信任賣家直達（露天・實查彙整）</h2>
  <div id="sellers"></div>

  <h2>🛡️ 防詐下單鐵則</h2>
  <div class="panel"><ol id="rules"></ol></div>

  <h2>📝 詢價範本（點右上複製，貼給賣家）</h2>
  <div class="panel tpl">
    <button class="copy" id="copyBtn">複製</button>
    <pre id="tpl"></pre>
  </div>

  <footer id="foot"></footer>
</div>

<script>
const APP = /*__APP_DATA__*/;
const $ = s => document.querySelector(s);
const enc = s => encodeURIComponent(s.trim());
let region = "all";

function currentKw(){ return $("#kw").value.trim(); }

function platformURL(p, kw){ return p.url.replace("{q}", enc(kw)); }

function renderPlatforms(){
  const kw = currentKw();
  const host = $("#platforms"); host.innerHTML = "";
  APP.platforms
    .filter(p => region === "all" || p.region === region)
    .forEach(p => {
      const regionTag = p.region === "tw"
        ? '<span class="tag tw">🇹🇼 台灣</span>'
        : '<span class="tag intl">🌐 國際</span>';
      const href = kw ? platformURL(p, kw) : "#";
      const cls = kw ? "pgo" : "pgo disabled";
      const label = kw ? ("在此搜尋「" + kw + "」 →") : "先輸入關鍵字";
      const el = document.createElement("div");
      el.className = "pcard";
      el.innerHTML =
        '<div class="ptop"><div class="rankb">'+p.rank+'</div><div class="pname">'+p.emoji+' '+p.name+'</div></div>'+
        '<div class="ptags">'+regionTag+'<span class="tag type">'+p.type+'</span></div>'+
        '<div class="pgood">👍 '+p.good+'</div>'+
        '<div class="prisk">⚠ '+p.risk+'</div>'+
        '<a class="'+cls+'" target="_blank" rel="noopener" href="'+href+'">'+label+'</a>';
      host.appendChild(el);
    });
}

function renderSellers(){
  const host = $("#sellers"); host.innerHTML = "";
  APP.trusted.forEach(s => {
    const url = "https://www.ruten.com.tw/store/"+s.account+"/";
    const el = document.createElement("div");
    el.className = "scard";
    el.innerHTML =
      '<div><div class="sname">'+s.name+' <span class="sacct">@'+s.account+'</span></div>'+
      '<div class="snote">'+s.note+'</div></div>'+
      '<a class="sgo" target="_blank" rel="noopener" href="'+url+'">前往賣場</a>';
    host.appendChild(el);
  });
}

function renderStatic(){
  $("#chips").innerHTML = APP.quick.map(k => '<span class="chip">'+k+'</span>').join("");
  $("#chips").querySelectorAll(".chip").forEach(c =>
    c.addEventListener("click", () => { $("#kw").value = c.textContent; renderPlatforms(); $("#kw").focus(); }));
  $("#rules").innerHTML = APP.rules.map(r => "<li>"+r+"</li>").join("");
  $("#tpl").textContent = APP.template;
  $("#avoid").innerHTML = "🚫 <b>避雷：</b>" + APP.avoid;
  $("#foot").innerHTML =
    "資料更新：" + APP.date + "　|　此工具只開啟各平台<b>真實搜尋</b>，不提供快取價格，價格以平台即時頁面為準。<br>"+
    "為個人比價與防詐用途整理，使用前請自行判斷賣家信用。一律貨到付款、收到先驗、不對拒收。";
}

// 一鍵詢價：依目前篩選，逐一開啟各平台搜尋（可能需允許彈出視窗）
$("#goAll").addEventListener("click", () => {
  const kw = currentKw();
  if(!kw){ $("#kw").focus(); return; }
  const list = APP.platforms.filter(p => region === "all" || p.region === region);
  // 第一個用本頁跳轉觸發，其餘開新分頁（降低被彈窗攔截機率仍建議逐張點卡片）
  list.forEach((p,i) => window.open(platformURL(p, kw), "_blank", "noopener"));
});

$("#kw").addEventListener("input", renderPlatforms);
$("#kw").addEventListener("keydown", e => { if(e.key === "Enter") $("#goAll").click(); });

document.querySelectorAll(".filt").forEach(f =>
  f.addEventListener("click", () => {
    document.querySelectorAll(".filt").forEach(x => x.classList.remove("on"));
    f.classList.add("on"); region = f.dataset.region; renderPlatforms();
  }));

$("#copyBtn").addEventListener("click", async () => {
  try{ await navigator.clipboard.writeText(APP.template);
    const b = $("#copyBtn"); b.textContent = "已複製 ✓"; b.classList.add("done");
    setTimeout(()=>{ b.textContent="複製"; b.classList.remove("done"); }, 1800);
  }catch(e){ alert("複製失敗，請手動選取。"); }
});

renderStatic(); renderSellers(); renderPlatforms();
</script>
</body>
</html>
"""


def main():
    if len(sys.argv) >= 2 and sys.argv[1] == "search":
        kw = " ".join(sys.argv[2:]).strip() or "i7-6700"
        cli_search(kw)
        return
    html = build_html()
    with open("index.html", "w", encoding="utf-8") as f:
        f.write(html)
    print("✅ 已產生 index.html（" + str(len(html)) + " bytes）")
    print("   本地預覽： python3 -m http.server 8000  然後開 http://localhost:8000")


if __name__ == "__main__":
    main()
