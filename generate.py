#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
二手電腦詢價系統 v2 — 產生器 (Python -> 靜態 HTML)
=================================================
單一資料來源 + 產生器。改下方常數或 content.json 後重跑即更新 index.html。

用法：
    python3 generate.py                      # 產生 index.html
    python3 generate.py search "i7-6700"       # 終端機列出各平台詢價直達連結

功能(v2)：一鍵多平台詢價 / 快速分類 / 載入 LINE txt 抓型號 / 拍照·上傳找零件 /
          規格相容檢查 + 比較表 / 精選賣家 + 賣價表 / 商業分析(五力·BMC·SWOT) /
          規則式 FAQ 客服 / 深色模式 / 一鍵全開書籤。
誠實原則：只開各平台「真實搜尋」，不爬價、不造假快取價。
"""

import json, sys, datetime
from urllib.parse import quote

# ── 全球前 10 大二手電腦平台（{q} 會被關鍵字取代；前端自動 URL 編碼）──────────
PLATFORMS = [
    {"rank":1,"name":"露天市集 Ruten","emoji":"🛒","region":"tw","type":"C2C 拍賣／賣場",
     "url":"https://www.ruten.com.tw/find/?q={q}","good":"台灣最大拍賣，二手零件、板U套最齊全","risk":"賣家良莠不齊，慎防標錯價／陸貨拆機，認評價數"},
    {"rank":2,"name":"Yahoo奇摩拍賣","emoji":"🟣","region":"tw","type":"C2C 拍賣",
     "url":"https://tw.bid.yahoo.com/search/auction/product?p={q}","good":"台灣老牌拍賣，個人出清二手多","risk":"介面較舊，賣家數比露天少"},
    {"rank":3,"name":"蝦皮購物 Shopee","emoji":"🦐","region":"tw","type":"電商／賣場",
     "url":"https://shopee.tw/search?keyword={q}","good":"量大、折價券多、店到店便宜","risk":"大量中國跨境拆機／充新，認『台灣現貨/出貨地』"},
    {"rank":4,"name":"旋轉拍賣 Carousell","emoji":"🔄","region":"tw","type":"C2C 二手",
     "url":"https://www.carousell.com.tw/search/{q}","good":"台灣在地個人二手出清，可議價、可面交","risk":"無平台金流保障時，盡量面交驗機"},
    {"rank":5,"name":"Facebook Marketplace／社團","emoji":"📘","region":"tw","type":"C2C 在地面交",
     "url":"https://www.facebook.com/marketplace/search/?query={q}","good":"在地面交、可當場驗機開機點亮最安心","risk":"私下交易無保障，只約公開場所、不先匯款"},
    {"rank":6,"name":"eBay","emoji":"🌐","region":"intl","type":"國際拍賣／二手",
     "url":"https://www.ebay.com/sch/i.html?_nkw={q}","good":"全球最大二手／整新市場，買家保護完整","risk":"國際運費＋關稅，到貨慢，注意可否寄台灣"},
    {"rank":7,"name":"Back Market","emoji":"♻️","region":"intl","type":"專業整新機",
     "url":"https://www.backmarket.com/en-us/search?q={q}","good":"歐美專業整新機平台，分級清楚、附保固","risk":"以筆電／手機為主，零件少；需國際運送"},
    {"rank":8,"name":"Swappa","emoji":"🤝","region":"intl","type":"二手 3C（美國）",
     "url":"https://swappa.com/search?q={q}","good":"美國二手 3C，上架前審核、買家保障佳","risk":"以筆電／手機／平板為主，主要寄美國境內"},
    {"rank":9,"name":"Amazon Renewed","emoji":"📦","region":"intl","type":"官方整新機",
     "url":"https://www.amazon.com/s?k={q}+renewed","good":"Amazon 認證整新，附 Renewed 保固","risk":"並非所有品項寄台灣，注意運送與保固範圍"},
    {"rank":10,"name":"Mercari 日本","emoji":"🇯🇵","region":"intl","type":"C2C 二手（日本）",
     "url":"https://jp.mercari.com/search?keyword={q}","good":"日本二手『美品』多、成色好","risk":"需日本集運轉送，溝通／運費成本較高"},
]
AVOID = "🇨🇳 閒魚／AliExpress 等中國平台、以及 X79/X99+Xeon E5『洋垃圾』伺服器板：便宜但無台灣保固、耗電、品質參差，文書看影片用不到，避開。"

# ── 常買零件快速分類 ──────────────────────────────────────────────
CATEGORIES = [
    {"key":"cpu","name":"CPU 處理器","emoji":"🧠","kw":"i7-6700 CPU"},
    {"key":"mb","name":"主機板","emoji":"🔲","kw":"H110M-K D3 主機板"},
    {"key":"ram","name":"記憶體","emoji":"📏","kw":"DDR4 8G 記憶體"},
    {"key":"ssd","name":"硬碟／SSD","emoji":"💾","kw":"SSD 256G 二手"},
    {"key":"psu","name":"電源供應器","emoji":"🔌","kw":"電源供應器 500W"},
    {"key":"gpu","name":"顯示卡","emoji":"🎮","kw":"RTX 3060 二手"},
    {"key":"pc","name":"整機","emoji":"🖥️","kw":"二手主機 文書"},
    {"key":"nb","name":"筆電","emoji":"💻","kw":"MacBook Pro 二手"},
]

# ── 信任賣家（露天，實查彙整 2026/6）────────────────────────────────
TRUSTED_SELLERS = [
    {"name":"桀鑫電腦","account":"js3c0800","note":"華碩 H110M-K D3 等 DDR3 板，評價約 2.1 萬、價格最低"},
    {"name":"JULE 3C會社","account":"jule1087","note":"華碩 H110M-C/A/E D3 款式齊、標良品，評價約 1.2 萬"},
    {"name":"知飾家","account":"ymy65668","note":"少數主打『真二手良品』台灣賣家，評價約 3,867"},
    {"name":"小圓二手拍賣","account":"jacky0930","note":"台廠華碩真二手板U，可沿用 i7-6700，評價約 3,080"},
    {"name":"光代電子","account":"el_zerg","note":"板U大賣場、含發票，評價全場最高（約 9,239）"},
]
PRICE_TABLES = [
    {"img":"assets/price-table-motherboard.png","title":"露天 1151 DDR3 主機板 — 賣家賣價表","desc":"單買主機板（適用 i7-6700 + DDR3L）"},
    {"img":"assets/price-table-combo.png","title":"露天 二手板U套（主機板+CPU+記憶體）前10名","desc":"整套換新平台的賣家比較"},
]

# ── 防詐下單鐵則 ──────────────────────────────────────────────────
RULES = [
    "一律「貨到付款」，收到先驗：開機點亮、CPU-Z 認型號，不對就<b>拒收</b>。",
    "認規格別只看標題：<b>LGA 腳位、DDR3／DDR4、D3／D4 版本</b>要對得上你的零件。",
    "下單前請賣家<b>白紙黑字確認「頁面價＝成交價」</b>，防『標錯價』事後反悔。",
    "先<b>確認現貨</b>，擋掉「下單後才說缺貨／改價」這招。",
    "簡體文案（主板／內存／臺式）＋淘寶圖＋引導加 LINE ＝ 中國跨境貨，留意保固。",
    "<b>評價數多、好評率 99%＋、開店久</b>優先；同型號多比 2–3 家，別只看最低價。",
    "貨到付款沒付錢前你<b>零風險</b>；賣家不出貨會被記『賣家未出貨』，責任在他。",
]
INQUIRY_TEMPLATE = """您好，想跟您確認這件商品，確認後馬上下單：
1. 規格是否正確？（腳位／記憶體版本／型號，例：LGA1151 + DDR3L，不是 DDR4）
2. 目前有現貨嗎？全新還是二手拆機？二手有測試過、正常開機點亮嗎？
3. 頁面標的價格就是最終成交價嗎？含運、貨到付款一共多少？
4. 有保固／七天測試良品嗎？收到不能用可否退換？
麻煩確認後再請您保留現貨，謝謝！"""
QUICK_KEYWORDS = ["i7-6700","H110M-K D3 主機板","DDR4 8G 記憶體","i5-9400F","RTX 3060","MacBook Pro 二手","二手主機 文書"]


def load_content():
    try:
        with open("content.json", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return {"parts":{"cpus":[],"boards":[],"ram":[],"rules":[]},"faq":{"items":[]},
                "fiveForces":{"forces":[]},"bmc":{"blocks":[]},
                "swot":{"strengths":[],"weaknesses":[],"opportunities":[],"threats":[]}}


def build_html():
    c = load_content()
    app = {
        "platforms":PLATFORMS,"avoid":AVOID,"categories":CATEGORIES,
        "trusted":TRUSTED_SELLERS,"priceTables":PRICE_TABLES,
        "rules":RULES,"template":INQUIRY_TEMPLATE,"quick":QUICK_KEYWORDS,
        "parts":c["parts"],"faq":c["faq"]["items"],
        "fiveForces":c["fiveForces"]["forces"],"bmc":c["bmc"]["blocks"],"swot":c["swot"],
        "date":datetime.date.today().isoformat(),
    }
    return HTML_TEMPLATE.replace("/*__APP_DATA__*/", json.dumps(app, ensure_ascii=False))


def cli_search(keyword):
    print("\n🔎 「%s」各平台詢價直達：\n" % keyword)
    for p in PLATFORMS:
        print("  %2d. %s\n      %s\n" % (p["rank"], p["name"], p["url"].replace("{q}", quote(keyword))))
    print("提醒：價格以各平台即時頁面為準；一律貨到付款、收到先驗、不對拒收。\n")


HTML_TEMPLATE = r"""<!DOCTYPE html>
<html lang="zh-Hant" data-theme="light">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>二手電腦詢價系統｜全球前10大平台一鍵比價・相容查詢・防詐客服</title>
<meta name="description" content="台灣二手電腦詢價系統：一鍵跳全球前10大平台真實搜尋比價、零件相容性檢查、規格比較表、商業分析、防詐 FAQ 客服、深色模式。">
<style>
:root{
 --bg:#f4f6fb;--card:#fff;--ink:#1f2430;--sub:#6b7280;--line:#e6e9f0;--accent:#2f5496;--accent2:#3b82f6;
 --tw:#16a34a;--intl:#7c3aed;--warn:#b91c1c;--chip:#eef2fb;--ok:#16a34a;--bad:#dc2626;
 --shadow:0 1px 3px rgba(16,24,40,.08),0 1px 2px rgba(16,24,40,.06);
}
[data-theme="dark"]{
 --bg:#0f1420;--card:#1a2030;--ink:#e8ecf4;--sub:#9aa3b2;--line:#2a3344;--accent:#5b8def;--accent2:#60a5fa;
 --tw:#34d399;--intl:#a78bfa;--warn:#f87171;--chip:#222b3d;--ok:#34d399;--bad:#f87171;
 --shadow:0 1px 3px rgba(0,0,0,.4);
}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--ink);line-height:1.6;-webkit-text-size-adjust:100%;
 font-family:-apple-system,"PingFang TC","Microsoft JhengHei",system-ui,"Segoe UI",sans-serif;transition:background .2s,color .2s}
.wrap{max-width:1060px;margin:0 auto;padding:14px 16px 70px}
header{display:flex;align-items:center;justify-content:space-between;gap:10px;padding:8px 0}
.brand{font-size:1.3rem;font-weight:800;letter-spacing:.5px}
.brand small{display:block;font-size:.72rem;color:var(--sub);font-weight:500;letter-spacing:0}
.theme{background:var(--card);border:1px solid var(--line);border-radius:10px;padding:8px 12px;cursor:pointer;color:var(--ink);font-size:1rem}
nav{position:sticky;top:0;z-index:30;background:var(--bg);display:flex;gap:6px;overflow-x:auto;padding:8px 0;margin-bottom:6px;-webkit-overflow-scrolling:touch}
nav button{flex:0 0 auto;border:1px solid var(--line);background:var(--card);color:var(--sub);border-radius:999px;
 padding:8px 14px;font-size:.9rem;font-weight:700;cursor:pointer;white-space:nowrap}
nav button.on{background:var(--accent);color:#fff;border-color:var(--accent)}
.view{display:none}.view.on{display:block;animation:fade .2s}
@keyframes fade{from{opacity:0;transform:translateY(4px)}to{opacity:1}}
h2{font-size:1.12rem;margin:22px 0 10px;display:flex;align-items:center;gap:8px}
h3{font-size:1rem;margin:16px 0 8px}
.muted{color:var(--sub);font-size:.86rem}
.searchrow{display:flex;gap:8px}
#kw{flex:1;font-size:1.05rem;padding:13px 14px;border:1.5px solid var(--line);border-radius:12px;background:var(--card);color:var(--ink);box-shadow:var(--shadow);outline:none}
#kw:focus{border-color:var(--accent2)}
.btn{border:0;border-radius:12px;padding:0 16px;font-size:1rem;font-weight:700;cursor:pointer;background:var(--accent);color:#fff;white-space:nowrap}
.btn:active{transform:translateY(1px)}
.btn.sec{background:var(--card);color:var(--accent);border:1px solid var(--line)}
.chips{display:flex;flex-wrap:wrap;gap:7px;margin-top:9px}
.chip{background:var(--chip);border:1px solid var(--line);color:var(--accent);padding:5px 11px;border-radius:999px;font-size:.85rem;cursor:pointer}
.cat{display:flex;align-items:center;gap:6px}
.filters{display:flex;gap:7px;margin:10px 0 2px}
.filt{flex:1;text-align:center;padding:8px;border:1px solid var(--line);border-radius:10px;background:var(--card);cursor:pointer;font-weight:600;font-size:.9rem;color:var(--sub)}
.filt.on{background:var(--accent);color:#fff;border-color:var(--accent)}
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(252px,1fr));gap:12px}
.card{background:var(--card);border:1px solid var(--line);border-radius:14px;padding:13px 14px;box-shadow:var(--shadow)}
.pcard{display:flex;flex-direction:column;gap:6px}
.ptop{display:flex;align-items:center;gap:9px}
.rankb{background:var(--accent);color:#fff;font-weight:800;font-size:.8rem;min-width:26px;height:26px;border-radius:8px;display:flex;align-items:center;justify-content:center}
.pname{font-weight:700;font-size:1rem;line-height:1.25}
.ptags{display:flex;flex-wrap:wrap;gap:5px;margin:2px 0}
.tag{font-size:.72rem;padding:2px 8px;border-radius:999px;font-weight:600}
.tag.tw{background:#dcfce7;color:#166534}.tag.intl{background:#ede9fe;color:#5b21b6}.tag.type{background:var(--chip);color:var(--accent)}
[data-theme="dark"] .tag.tw{background:#0c3a26}[data-theme="dark"] .tag.intl{background:#2e1d54}
.pgood{font-size:.86rem}.prisk{font-size:.8rem;color:var(--warn)}
.pgo{margin-top:6px;text-align:center;text-decoration:none;font-weight:700;font-size:.95rem;background:var(--accent2);color:#fff;padding:9px;border-radius:10px;display:block}
.pgo.disabled{background:#9aa6b8;pointer-events:none}
.tools{display:grid;grid-template-columns:repeat(auto-fit,minmax(250px,1fr));gap:10px;margin:10px 0}
.scard{display:flex;justify-content:space-between;align-items:center;gap:10px;margin-bottom:9px}
.sname{font-weight:700}.sacct{color:var(--sub);font-size:.8rem}.snote{font-size:.84rem;color:var(--sub)}
.sgo{text-decoration:none;background:var(--tw);color:#fff;font-weight:700;padding:8px 13px;border-radius:9px;white-space:nowrap;font-size:.88rem}
.imgwrap img{width:100%;border-radius:12px;border:1px solid var(--line);display:block}
.panel ol{margin:0;padding-left:1.25rem}.panel li{margin:6px 0;font-size:.92rem}
.tpl{position:relative}
pre{white-space:pre-wrap;background:#0f172a;color:#e2e8f0;border-radius:12px;padding:14px;font-size:.86rem;line-height:1.7;margin:0;font-family:inherit}
.copy{position:absolute;top:10px;right:10px;background:#334155;color:#fff;border:0;border-radius:8px;padding:6px 11px;font-size:.8rem;cursor:pointer;font-weight:700}
.copy.done{background:var(--tw)}
.avoid{margin-top:10px;background:#fef2f2;border:1px solid #fecaca;color:#7f1d1d;border-radius:12px;padding:11px 14px;font-size:.86rem}
[data-theme="dark"] .avoid{background:#3a1414;border-color:#7f1d1d;color:#fca5a5}
table{width:100%;border-collapse:collapse;font-size:.84rem;background:var(--card);border-radius:12px;overflow:hidden;box-shadow:var(--shadow)}
th,td{border:1px solid var(--line);padding:8px 9px;text-align:left;vertical-align:top}
th{background:var(--accent);color:#fff;font-weight:700;position:sticky}
.tblscroll{overflow-x:auto;margin:8px 0}
select,input[type=text]{width:100%;padding:10px;border:1px solid var(--line);border-radius:10px;background:var(--card);color:var(--ink);font-size:.95rem}
label.fld{display:block;font-size:.82rem;color:var(--sub);margin:8px 0 3px}
.verdict{margin-top:10px;padding:13px 15px;border-radius:12px;font-size:.92rem}
.verdict.ok{background:#dcfce7;border:1px solid #86efac;color:#166534}
.verdict.bad{background:#fee2e2;border:1px solid #fca5a5;color:#991b1b}
[data-theme="dark"] .verdict.ok{background:#0c3a26;color:#86efac}[data-theme="dark"] .verdict.bad{background:#3a1414;color:#fca5a5}
.verdict ul{margin:6px 0 0;padding-left:1.2rem}
.bmc{display:grid;grid-template-columns:repeat(5,1fr);grid-auto-rows:minmax(70px,auto);gap:8px}
.bmc .b{background:var(--card);border:1px solid var(--line);border-radius:10px;padding:9px;font-size:.78rem;box-shadow:var(--shadow)}
.bmc .b b{display:block;font-size:.8rem;margin-bottom:4px;color:var(--accent)}
.bmc .b ul{margin:0;padding-left:1rem}.bmc .b li{margin:2px 0}
.b-kp{grid-row:span 2}.b-vp{grid-row:span 2}.b-cs{grid-row:span 2}
.swot{display:grid;grid-template-columns:1fr 1fr;gap:10px}
.sw{border-radius:12px;padding:12px 14px;font-size:.85rem;border:1px solid var(--line)}
.sw b{display:block;margin-bottom:5px}.sw ul{margin:0;padding-left:1.1rem}.sw li{margin:3px 0}
.sw.s{background:#ecfdf5}.sw.w{background:#fff7ed}.sw.o{background:#eff6ff}.sw.t{background:#fef2f2}
[data-theme="dark"] .sw.s{background:#0c2a1e}[data-theme="dark"] .sw.w{background:#2a1f10}[data-theme="dark"] .sw.o{background:#10243f}[data-theme="dark"] .sw.t{background:#2a1414}
.faqchat{background:var(--card);border:1px solid var(--line);border-radius:14px;padding:12px;box-shadow:var(--shadow)}
.bubble{padding:10px 13px;border-radius:12px;margin:8px 0;font-size:.9rem;white-space:pre-wrap}
.bubble.me{background:var(--accent);color:#fff;margin-left:auto;max-width:85%}
.bubble.bot{background:var(--chip);max-width:92%}
.faqitem{border:1px solid var(--line);border-radius:10px;margin:7px 0;background:var(--card);overflow:hidden}
.faqq{padding:11px 13px;font-weight:700;cursor:pointer;font-size:.9rem;display:flex;justify-content:space-between;gap:8px}
.faqa{padding:0 13px;max-height:0;overflow:hidden;white-space:pre-wrap;font-size:.86rem;color:var(--sub);transition:max-height .25s,padding .25s}
.faqitem.open .faqa{max-height:600px;padding:0 13px 12px}
.camwrap{display:flex;flex-direction:column;gap:8px}
video,canvas#shot{width:100%;max-height:280px;border-radius:12px;border:1px solid var(--line);background:#000}
#photo{max-width:100%;border-radius:12px;border:1px solid var(--line)}
.note{font-size:.8rem;color:var(--sub);background:var(--chip);border-radius:10px;padding:9px 12px;margin-top:8px}
footer{margin-top:34px;text-align:center;color:var(--sub);font-size:.8rem;line-height:1.7}
.radarbox{display:flex;flex-wrap:wrap;gap:14px;align-items:center;justify-content:center}
@media(max-width:680px){.bmc{grid-template-columns:1fr 1fr}.b-kp,.b-vp,.b-cs{grid-row:auto}.swot{grid-template-columns:1fr}}
@media(max-width:520px){.brand{font-size:1.1rem}}
</style>
</head>
<body>
<div class="wrap">
 <header>
  <div class="brand">🖥️ 二手電腦詢價系統<small>全球前10大平台比價・相容查詢・防詐客服</small></div>
  <button class="theme" id="themeBtn" title="深色／淺色">🌙</button>
 </header>
 <nav id="nav">
  <button data-v="find" class="on">🔎 詢價比價</button>
  <button data-v="sellers">✅ 精選賣家</button>
  <button data-v="compat">🧩 規格相容</button>
  <button data-v="photo">📷 拍照找件</button>
  <button data-v="biz">📊 商業分析</button>
  <button data-v="faq">💬 FAQ客服</button>
 </nav>

 <!-- 詢價 -->
 <section class="view on" id="find">
  <div class="searchrow">
   <input id="kw" type="search" placeholder="輸入型號或品名，例：i7-6700、H110M-K D3、MacBook Pro" autocomplete="off">
   <button class="btn" id="goAll">一鍵全開</button>
  </div>
  <div class="chips" id="cats"></div>
  <div class="chips" id="chips"></div>
  <div class="filters">
   <div class="filt on" data-region="all">全部</div>
   <div class="filt" data-region="tw">🇹🇼 台灣平台</div>
   <div class="filt" data-region="intl">🌐 國際／整新</div>
  </div>
  <div class="tools">
   <label class="btn sec" style="text-align:center;cursor:pointer">📂 載入 LINE 對話 txt 抓型號
    <input type="file" id="lineFile" accept=".txt" hidden></label>
   <a class="btn sec" id="bmk" style="text-align:center" href="#" title="拖到書籤列">⭐ 一鍵比價書籤（拖到書籤列）</a>
  </div>
  <div id="lineOut"></div>
  <h2>🏆 全球前 10 大二手電腦平台</h2>
  <div class="grid" id="platforms"></div>
  <div class="avoid" id="avoid"></div>
  <h2>🛡️ 防詐下單鐵則</h2>
  <div class="card panel"><ol id="rules"></ol></div>
  <h2>📝 詢價範本</h2>
  <div class="card tpl"><button class="copy" id="copyBtn">複製</button><pre id="tpl"></pre></div>
 </section>

 <!-- 精選賣家 -->
 <section class="view" id="sellers">
  <h2>✅ 信任賣家直達（露天・實查彙整）</h2>
  <div id="sellerList"></div>
  <h2>📋 賣價對照表</h2>
  <div id="priceTables"></div>
 </section>

 <!-- 規格相容 -->
 <section class="view" id="compat">
  <h2>🧩 零件相容性檢查</h2>
  <div class="card">
   <label class="fld">CPU 處理器</label><select id="cCpu"></select>
   <label class="fld">主機板</label><select id="cBoard"></select>
   <label class="fld">記憶體類型</label>
   <select id="cRam"><option value="">（先不選）</option><option>DDR3</option><option>DDR3L</option><option>DDR4</option></select>
   <button class="btn" id="cGo" style="margin-top:12px;width:100%">檢查相容性</button>
   <div id="cResult"></div>
  </div>
  <h2>📐 規格比較表</h2>
  <p class="muted">勾選下方零件，產生規格比較表。</p>
  <button class="btn sec" id="cmpGo">產生比較表</button>
  <div id="cmpOut"></div>
  <h3>CPU 規格庫</h3><div class="tblscroll" id="cpuTbl"></div>
  <h3>主機板規格庫</h3><div class="tblscroll" id="boardTbl"></div>
  <h3>記憶體規格</h3><div class="tblscroll" id="ramTbl"></div>
  <h2>📏 相容性判斷規則</h2><div class="card panel"><ol id="partRules"></ol></div>
 </section>

 <!-- 拍照找件 -->
 <section class="view" id="photo">
  <h2>📷 拍照／上傳 找相容零件</h2>
  <div class="card camwrap">
   <div class="searchrow">
    <label class="btn sec" style="flex:1;text-align:center;cursor:pointer">🖼️ 上傳照片
     <input type="file" id="upPhoto" accept="image/*" capture="environment" hidden></label>
    <button class="btn sec" id="camBtn" style="flex:1">📸 開啟相機</button>
   </div>
   <video id="cam" autoplay playsinline style="display:none"></video>
   <button class="btn" id="shotBtn" style="display:none">拍照</button>
   <canvas id="shot" style="display:none"></canvas>
   <img id="photo" style="display:none" alt="預覽">
   <label class="fld">輸入照片上看到的型號（晶片/主板絲印），自動查相容＋比價</label>
   <input type="text" id="photoModel" placeholder="例：i7-6700、H110M-K D3、DDR3L 8G">
   <div class="searchrow" style="margin-top:8px">
    <button class="btn" id="photoFind" style="flex:1">🔎 拿去比價</button>
    <a class="btn sec" id="lens" style="flex:1;text-align:center" target="_blank" rel="noopener" href="https://lens.google.com/">🔍 Google Lens 以圖搜尋</a>
   </div>
   <div class="note">⚠️ 誠實說明：純靜態網站<b>無法自動辨識</b>照片裡的晶片（那需要 AI 後端）。這裡做的是「拍照／上傳留存 ＋ 你輸入型號 → 自動查相容性＋一鍵比價」，並可用 Google Lens 以圖搜尋型號。要真‧自動辨識可再接 AI API（升級項）。</div>
  </div>
 </section>

 <!-- 商業分析 -->
 <section class="view" id="biz">
  <h2>📊 波特五力分析（本系統）</h2>
  <div class="card radarbox"><div id="radar"></div><div id="forceList" style="flex:1;min-width:260px"></div></div>
  <h2>🧱 商業模式圖 BMC</h2>
  <div class="bmc" id="bmc"></div>
  <h2>🎯 SWOT 分析</h2>
  <div class="swot" id="swot"></div>
 </section>

 <!-- FAQ -->
 <section class="view" id="faq">
  <h2>💬 規則式 FAQ 客服</h2>
  <div class="note">這是用本專案知識庫做的<b>關鍵字比對機器人</b>（非真 AI）。問「DDR3L 能用嗎」「賣家叫我取消」「嗶兩聲沒畫面」等都行。要接真 AI 需 API 後端。</div>
  <div class="faqchat" style="margin-top:10px">
   <div id="chatlog"></div>
   <div class="searchrow" style="margin-top:8px">
    <input id="askIn" type="text" placeholder="輸入你的問題…">
    <button class="btn" id="askBtn">問</button>
   </div>
  </div>
  <h2>📚 常見問題（點開看答案）</h2>
  <div id="faqList"></div>
 </section>

 <footer id="foot"></footer>
</div>

<script>
const APP = /*__APP_DATA__*/;
const $=s=>document.querySelector(s), $$=s=>[...document.querySelectorAll(s)];
const enc=s=>encodeURIComponent((s||"").trim());
const esc=s=>(s||"").replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;");
let region="all";

/* ---------- theme ---------- */
function setTheme(t){document.documentElement.dataset.theme=t;$("#themeBtn").textContent=t==="dark"?"☀️":"🌙";try{localStorage.setItem("pcf-theme",t)}catch(e){}}
$("#themeBtn").onclick=()=>setTheme(document.documentElement.dataset.theme==="dark"?"light":"dark");
(function(){let t;try{t=localStorage.getItem("pcf-theme")}catch(e){}; if(!t)t=matchMedia("(prefers-color-scheme: dark)").matches?"dark":"light"; setTheme(t);})();

/* ---------- nav ---------- */
$$("#nav button").forEach(b=>b.onclick=()=>{
 $$("#nav button").forEach(x=>x.classList.remove("on"));b.classList.add("on");
 $$(".view").forEach(v=>v.classList.remove("on"));$("#"+b.dataset.v).classList.add("on");
 window.scrollTo(0,0);
});

/* ---------- 詢價 ---------- */
const kwOf=()=>$("#kw").value.trim();
const purl=(p,k)=>p.url.replace("{q}",enc(k));
function renderPlatforms(){
 const k=kwOf(),h=$("#platforms");h.innerHTML="";
 APP.platforms.filter(p=>region==="all"||p.region===region).forEach(p=>{
  const rt=p.region==="tw"?'<span class="tag tw">🇹🇼 台灣</span>':'<span class="tag intl">🌐 國際</span>';
  const href=k?purl(p,k):"#",cls=k?"pgo":"pgo disabled",lab=k?("在此搜尋「"+esc(k)+"」 →"):"先輸入關鍵字";
  const d=document.createElement("div");d.className="card pcard";
  d.innerHTML='<div class="ptop"><div class="rankb">'+p.rank+'</div><div class="pname">'+p.emoji+' '+esc(p.name)+'</div></div>'+
   '<div class="ptags">'+rt+'<span class="tag type">'+esc(p.type)+'</span></div>'+
   '<div class="pgood">👍 '+esc(p.good)+'</div><div class="prisk">⚠ '+esc(p.risk)+'</div>'+
   '<a class="'+cls+'" target="_blank" rel="noopener" href="'+href+'">'+lab+'</a>';
  h.appendChild(d);
 });
 updateBookmarklet();
}
function setKw(v){$("#kw").value=v;renderPlatforms();}
$("#kw").addEventListener("input",renderPlatforms);
$("#kw").addEventListener("keydown",e=>{if(e.key==="Enter")$("#goAll").click()});
$("#goAll").onclick=()=>{const k=kwOf();if(!k){$("#kw").focus();return;}
 APP.platforms.filter(p=>region==="all"||p.region===region).forEach(p=>window.open(purl(p,k),"_blank","noopener"));};
$$(".filt").forEach(f=>f.onclick=()=>{$$(".filt").forEach(x=>x.classList.remove("on"));f.classList.add("on");region=f.dataset.region;renderPlatforms();});
function updateBookmarklet(){
 const urls=APP.platforms.filter(p=>p.region==="tw").map(p=>p.url.replace("{q}","'+q+'"));
 const code="javascript:(function(){var q=encodeURIComponent(prompt('二手電腦比價，要找什麼？'));if(!q)return;["+
  urls.map(u=>"'"+u+"'").join(",")+"].forEach(function(u){window.open(u,'_blank')})})()";
 $("#bmk").setAttribute("href",code);
}

/* ---------- LINE txt 解析 ---------- */
const PART_RE=[/\bi[3579]-?\d{3,5}[A-Z]{0,2}\b/gi,/\b[HBZQ]\d{2,3}M?(?:-?[A-Z0-9]{1,6})?\b/g,
 /\bDDR[345]L?(?:-?\d{3,4})?\b/gi,/\bRTX\s?\d{3,4}(?:\s?Ti)?\b/gi,/\bGTX\s?\d{3,4}(?:\s?Ti)?\b/gi,
 /\bRyzen\s?\d\s?\d{3,4}[A-Z]{0,3}\b/gi,/\bRX\s?\d{3,4}\b/gi,/\bLGA\s?\d{3,4}\b/gi,/\bMacBook(?:\s?(?:Pro|Air))?\b/gi];
$("#lineFile").addEventListener("change",e=>{
 const f=e.target.files[0];if(!f)return;const r=new FileReader();
 r.onload=()=>{
  const txt=r.result;const found={};
  PART_RE.forEach(re=>{let m;while((m=re.exec(txt))){const v=m[0].trim();if(v.length>=3)found[v.toUpperCase()]=v;}});
  const list=Object.values(found).slice(0,40);
  const out=$("#lineOut");
  if(!list.length){out.innerHTML='<div class="note">沒在這個 txt 裡找到明顯的電腦零件型號。</div>';return;}
  out.innerHTML='<div class="note">從 LINE 對話抓到 '+list.length+' 個型號，點一下就帶去比價：</div><div class="chips">'+
   list.map(v=>'<span class="chip" data-k="'+esc(v)+'">'+esc(v)+'</span>').join("")+'</div>';
  out.querySelectorAll(".chip").forEach(c=>c.onclick=()=>{setKw(c.dataset.k);$("#kw").scrollIntoView({block:"center"});});
 };
 r.readAsText(f);
});

/* ---------- 精選賣家 ---------- */
function renderSellers(){
 const h=$("#sellerList");h.innerHTML="";
 APP.trusted.forEach(s=>{
  const d=document.createElement("div");d.className="card scard";
  d.innerHTML='<div><div class="sname">'+esc(s.name)+' <span class="sacct">@'+esc(s.account)+'</span></div><div class="snote">'+esc(s.note)+'</div></div>'+
   '<a class="sgo" target="_blank" rel="noopener" href="https://www.ruten.com.tw/store/'+esc(s.account)+'/">前往賣場</a>';
  h.appendChild(d);
 });
 $("#priceTables").innerHTML=APP.priceTables.map(t=>
  '<div class="card" style="margin-bottom:12px"><b>'+esc(t.title)+'</b><div class="muted" style="margin:2px 0 8px">'+esc(t.desc)+'</div>'+
  '<div class="imgwrap"><a href="'+t.img+'" target="_blank" rel="noopener"><img src="'+t.img+'" alt="'+esc(t.title)+'" loading="lazy"></a></div></div>').join("");
}

/* ---------- 規格相容 ---------- */
function classifyBoard(b){const c=(b.chipset||"")+" "+(b.model||"");
 if(/B360|B365|H310|H370|Z370|Z390|B460|H410/.test(c))return{sock:"LGA1151",gens:[8,9]};
 if(/H110|B150|H170|Z170|B250|Z270|Q150|Q170/.test(c))return{sock:"LGA1151",gens:[6,7]};
 if(/B85|H81|H97|Z97|H61|B75|Q87/.test(c))return{sock:"LGA1150",gens:[4]};
 return{sock:b.socket||"",gens:[]};}
const genNum=cpu=>{const m=(cpu.gen||"").match(/第\s*(\d+)\s*代/);return m?+m[1]:null;};
const memFlags=s=>({d3:/DDR3/i.test(s||""),d4:/DDR4/i.test(s||"")});
function evalCompat(cpu,board,ram){
 const reasons=[],warn=[];let ok=true;const bs=classifyBoard(board);
 if(cpu.socket&&bs.sock&&cpu.socket!==bs.sock){ok=false;reasons.push("腳位不符：CPU "+cpu.socket+"，主機板 "+bs.sock+"，針腳對不上。");}
 else{const g=genNum(cpu);if(bs.gens.length&&g&&bs.gens.indexOf(g)<0){ok=false;reasons.push("晶片組世代不符：CPU 第"+g+"代，但 "+board.chipset+" 支援第 "+bs.gens.join("/")+" 代。");}}
 const bm=memFlags(board.mem_type),cm=memFlags(cpu.mem_support);
 const kind=bm.d3&&!bm.d4?"DDR3／DDR3L":(bm.d4?"DDR4":"未知");
 if(ram){
  if(ram==="DDR4"&&!bm.d4){ok=false;reasons.push("記憶體不相容：主機板吃 "+kind+"，DDR4 插不上。");}
  if((ram==="DDR3"||ram==="DDR3L")&&!bm.d3){ok=false;reasons.push("記憶體不相容：主機板吃 "+kind+"，"+ram+" 插不上。");}
  if(ram==="DDR4"&&!cm.d4){ok=false;reasons.push("CPU "+cpu.model+" 不支援 DDR4。");}
  if((ram==="DDR3"||ram==="DDR3L")&&!cm.d3){ok=false;reasons.push("CPU "+cpu.model+" 不支援 DDR3／DDR3L。");}
  if(ok&&ram==="DDR3L"&&bm.d3)warn.push("DDR3L(1.35V) 正是 6/7 代搭 D3 板的建議選擇，放心用。");
 }
 if(/\d+F\b/.test(cpu.model))warn.push("CPU 尾碼 F 沒有內顯，要另配獨立顯示卡才有畫面。");
 if(ok&&!ram)warn.push("提示：主機板吃 "+kind+"，記住買對應的記憶體版本。");
 return{ok,reasons,warn,kind};
}
function fillSelect(id,arr,fn){$(id).innerHTML=arr.map((x,i)=>'<option value="'+i+'">'+esc(fn(x))+'</option>').join("");}
function renderCompat(){
 fillSelect("#cCpu",APP.parts.cpus,c=>c.model+"（"+c.socket+"・"+(c.gen||"")+"）");
 fillSelect("#cBoard",APP.parts.boards,b=>b.model+"（"+b.chipset+"・"+b.mem_type+"）");
 $("#cGo").onclick=()=>{
  const cpu=APP.parts.cpus[+$("#cCpu").value],board=APP.parts.boards[+$("#cBoard").value],ram=$("#cRam").value;
  const r=evalCompat(cpu,board,ram);
  let html='<div class="verdict '+(r.ok?"ok":"bad")+'"><b>'+(r.ok?"✅ 可相容":"❌ 不相容")+'</b>';
  if(r.reasons.length)html+='<ul>'+r.reasons.map(x=>"<li>"+esc(x)+"</li>").join("")+'</ul>';
  if(r.warn.length)html+='<ul>'+r.warn.map(x=>"<li>⚠ "+esc(x)+"</li>").join("")+'</ul>';
  html+='</div>';$("#cResult").innerHTML=html;
 };
 // tables with compare checkboxes
 $("#cpuTbl").innerHTML=tbl(["","型號","腳位","世代","核心緒","TDP","記憶體支援"],
  APP.parts.cpus.map((c,i)=>['<input type="checkbox" data-t="cpu" data-i="'+i+'">',c.model,c.socket,c.gen||"",c.cores_threads,c.tdp,c.mem_support]));
 $("#boardTbl").innerHTML=tbl(["","型號","腳位","晶片組","記憶體","插槽","最大","板型"],
  APP.parts.boards.map((b,i)=>['<input type="checkbox" data-t="board" data-i="'+i+'">',b.model,b.socket,b.chipset,b.mem_type,b.mem_slots||"",b.max_mem||"",b.form_factor||""]));
 $("#ramTbl").innerHTML=tbl(["類型","電壓","插槽","說明"],APP.parts.ram.map(r=>[r.type,r.voltage,r.slot||"",r.note]));
 $("#partRules").innerHTML=APP.parts.rules.map(r=>"<li>"+esc(r)+"</li>").join("");
}
function tbl(head,rows){
 return '<table><thead><tr>'+head.map(h=>"<th>"+esc(h)+"</th>").join("")+'</tr></thead><tbody>'+
  rows.map(r=>"<tr>"+r.map((c,i)=>"<td>"+(i===0&&/^<input/.test(c)?c:esc(String(c)))+"</td>").join("")+"</tr>").join("")+'</tbody></table>';
}
$("#cmpGo").onclick=()=>{
 const picks=$$("#compat input[type=checkbox]:checked").map(c=>({t:c.dataset.t,i:+c.dataset.i}));
 if(!picks.length){$("#cmpOut").innerHTML='<div class="note">先在下面勾選要比較的零件。</div>';return;}
 const rows=picks.map(p=>{const x=p.t==="cpu"?APP.parts.cpus[p.i]:APP.parts.boards[p.i];
  return p.t==="cpu"?[x.model,"CPU",x.socket,x.gen||"",x.cores_threads,x.tdp,x.mem_support,x.note||""]
   :[x.model,"主機板",x.socket,x.chipset,x.form_factor||"",x.max_mem||"",x.mem_type,x.note||""];});
 $("#cmpOut").innerHTML='<div class="tblscroll">'+tbl(["型號","類型","腳位","世代/晶片組","核緒/板型","TDP/最大","記憶體","備註"],rows)+'</div>';
 $("#cmpOut").scrollIntoView({block:"start"});
};

/* ---------- 拍照 ---------- */
let stream=null;
$("#upPhoto").addEventListener("change",e=>{const f=e.target.files[0];if(!f)return;
 const img=$("#photo");img.src=URL.createObjectURL(f);img.style.display="block";});
$("#camBtn").onclick=async()=>{
 try{stream=await navigator.mediaDevices.getUserMedia({video:{facingMode:"environment"}});
  const v=$("#cam");v.srcObject=stream;v.style.display="block";$("#shotBtn").style.display="block";
 }catch(e){alert("無法開啟相機："+e.message+"\n可改用『上傳照片』。");}
};
$("#shotBtn").onclick=()=>{const v=$("#cam"),cv=$("#shot");cv.width=v.videoWidth;cv.height=v.videoHeight;
 cv.getContext("2d").drawImage(v,0,0);const img=$("#photo");img.src=cv.toDataURL("image/jpeg",.9);img.style.display="block";
 if(stream){stream.getTracks().forEach(t=>t.stop());}v.style.display="none";$("#shotBtn").style.display="none";};
$("#photoFind").onclick=()=>{const m=$("#photoModel").value.trim();if(!m){$("#photoModel").focus();return;}
 setKw(m);$$("#nav button").forEach(x=>x.classList.remove("on"));$('#nav button[data-v=find]').classList.add("on");
 $$(".view").forEach(v=>v.classList.remove("on"));$("#find").classList.add("on");window.scrollTo(0,0);};

/* ---------- 商業分析 ---------- */
function renderBiz(){
 // radar
 const F=APP.fiveForces,n=F.length,cx=150,cy=150,R=110;
 const pt=(i,r)=>{const a=-Math.PI/2+i*2*Math.PI/n;return[cx+r*Math.cos(a),cy+r*Math.sin(a)];};
 let g="";for(let ring=1;ring<=5;ring++){const pts=F.map((_,i)=>pt(i,R*ring/5).join(",")).join(" ");
  g+='<polygon points="'+pts+'" fill="none" stroke="var(--line)"/>';}
 F.forEach((_,i)=>{const e=pt(i,R);g+='<line x1="'+cx+'" y1="'+cy+'" x2="'+e[0]+'" y2="'+e[1]+'" stroke="var(--line)"/>';});
 const dp=F.map((f,i)=>pt(i,R*f.score/5).join(",")).join(" ");
 g+='<polygon points="'+dp+'" fill="rgba(59,130,246,.35)" stroke="var(--accent2)" stroke-width="2"/>';
 F.forEach((f,i)=>{const e=pt(i,R+18);g+='<text x="'+e[0]+'" y="'+e[1]+'" font-size="10" fill="var(--ink)" text-anchor="middle">'+esc(f.name.replace(/\(.*?\)/g,""))+' '+f.score+'</text>';});
 $("#radar").innerHTML='<svg viewBox="0 0 300 300" width="300" height="300">'+g+'</svg>';
 $("#forceList").innerHTML=F.map(f=>'<div style="margin:8px 0"><b>'+esc(f.name)+'（壓力 '+f.score+'/5）</b><div class="muted">'+esc(f.summary)+'</div></div>').join("");
 // BMC layout
 const order=["keyPartners","keyActivities","valueProps","customerRelationships","customerSegments","keyResources","channels","costStructure","revenueStreams"];
 const cls={keyPartners:"b-kp",valueProps:"b-vp",customerSegments:"b-cs"};
 const map={};APP.bmc.forEach(b=>map[b.key]=b);
 $("#bmc").innerHTML=order.map(k=>{const b=map[k];if(!b)return"";
  return '<div class="b '+(cls[k]||"")+'"><b>'+esc(b.title)+'</b><ul>'+b.items.map(i=>"<li>"+esc(i)+"</li>").join("")+'</ul></div>';}).join("");
 // SWOT
 const S=APP.swot,box=(t,c,a)=>'<div class="sw '+c+'"><b>'+t+'</b><ul>'+a.map(i=>"<li>"+esc(i)+"</li>").join("")+'</ul></div>';
 $("#swot").innerHTML=box("💪 優勢 S","s",S.strengths)+box("⚠️ 劣勢 W","w",S.weaknesses)+box("🚀 機會 O","o",S.opportunities)+box("⛓️ 威脅 T","t",S.threats);
}

/* ---------- FAQ ---------- */
function matchFaq(q){
 q=(q||"").toLowerCase();let best=null,bs=0;
 APP.faq.forEach(it=>{let s=0;(it.keywords||[]).forEach(k=>{if(q.includes(k.toLowerCase()))s+=2;});
  if(q&&it.q.toLowerCase().includes(q))s+=1;if(s>bs){bs=s;best=it;}});
 return bs>0?best:null;
}
function chat(role,txt){const d=document.createElement("div");d.className="bubble "+role;d.textContent=txt;$("#chatlog").appendChild(d);
 $("#chatlog").lastChild.scrollIntoView({block:"end"});}
$("#askBtn").onclick=()=>{const q=$("#askIn").value.trim();if(!q)return;chat("me",q);$("#askIn").value="";
 const m=matchFaq(q);
 if(m)chat("bot","【"+m.q+"】\n"+m.a);
 else chat("bot","這題我的知識庫沒有直接答案。試試關鍵字：DDR3L、DDR4、標錯價、不出貨、嗶兩聲、挑賣家、洋垃圾、驗機。也可往下看『常見問題』。");
};
$("#askIn").addEventListener("keydown",e=>{if(e.key==="Enter")$("#askBtn").click()});
function renderFaqList(){
 $("#faqList").innerHTML=APP.faq.map((it,i)=>'<div class="faqitem" data-i="'+i+'"><div class="faqq">'+esc(it.q)+'<span>＋</span></div><div class="faqa">'+esc(it.a)+'</div></div>').join("");
 $$("#faqList .faqitem").forEach(el=>el.querySelector(".faqq").onclick=()=>el.classList.toggle("open"));
}

/* ---------- static ---------- */
function renderStatic(){
 $("#cats").innerHTML=APP.categories.map(c=>'<span class="chip cat" data-k="'+esc(c.kw)+'">'+c.emoji+' '+esc(c.name)+'</span>').join("");
 $("#cats").querySelectorAll(".chip").forEach(c=>c.onclick=()=>{setKw(c.dataset.k);$("#kw").focus();});
 $("#chips").innerHTML='<span class="muted" style="align-self:center">常搜：</span>'+APP.quick.map(k=>'<span class="chip" data-k="'+esc(k)+'">'+esc(k)+'</span>').join("");
 $("#chips").querySelectorAll(".chip").forEach(c=>c.onclick=()=>{setKw(c.dataset.k);$("#kw").focus();});
 $("#rules").innerHTML=APP.rules.map(r=>"<li>"+r+"</li>").join("");
 $("#tpl").textContent=APP.template;
 $("#avoid").innerHTML="🚫 <b>避雷：</b>"+esc(APP.avoid);
 $("#foot").innerHTML="資料更新："+APP.date+"　|　只開各平台<b>真實搜尋</b>，不爬價、不造假快取價，價格以平台即時頁面為準。<br>個人比價與防詐用途，使用前自行判斷賣家信用。一律貨到付款、收到先驗、不對拒收。<br>🤖 以 Claude Code 製作";
}
$("#copyBtn").onclick=async()=>{try{await navigator.clipboard.writeText(APP.template);
 const b=$("#copyBtn");b.textContent="已複製 ✓";b.classList.add("done");setTimeout(()=>{b.textContent="複製";b.classList.remove("done");},1800);
}catch(e){alert("複製失敗，請手動選取。");}};

renderStatic();renderPlatforms();renderSellers();renderCompat();renderBiz();renderFaqList();
</script>
</body>
</html>
"""


def main():
    if len(sys.argv) >= 2 and sys.argv[1] == "search":
        cli_search(" ".join(sys.argv[2:]).strip() or "i7-6700")
        return
    html = build_html()
    with open("index.html", "w", encoding="utf-8") as f:
        f.write(html)
    print("✅ 已產生 index.html（%d bytes）" % len(html))
    print("   本地預覽： python3 -m http.server 8000  →  http://localhost:8000")


if __name__ == "__main__":
    main()
