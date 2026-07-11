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
    try:
        consult = json.load(open("consult.json", encoding="utf-8"))
    except FileNotFoundError:
        consult = {}
    try:
        research = json.load(open("research.json", encoding="utf-8"))
    except FileNotFoundError:
        research = {}
    app = {
        "platforms":PLATFORMS,"avoid":AVOID,"categories":CATEGORIES,
        "trusted":TRUSTED_SELLERS,"priceTables":PRICE_TABLES,
        "rules":RULES,"template":INQUIRY_TEMPLATE,"quick":QUICK_KEYWORDS,
        "parts":c["parts"],"faq":c["faq"]["items"],
        "fiveForces":c["fiveForces"]["forces"],"bmc":c["bmc"]["blocks"],"swot":c["swot"],
        "consult":consult,
        "research":research,
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
 /* 護眼淺色:低藍光暖底、柔和對比(WCAG AA 以上) */
 --bg:#eef0e4;--card:#faf9f0;--ink:#2f3428;--sub:#67705c;--line:#dcdfcd;--accent:#31694d;--accent2:#3d7d5f;
 --tw:#2e7d4f;--intl:#6d5fa8;--warn:#a33a2a;--chip:#e7ecdb;--ok:#2e7d4f;--bad:#b3402e;
 --shadow:0 1px 3px rgba(47,52,40,.08),0 1px 2px rgba(47,52,40,.05);
 /* 圖表類別色(已通過 CVD/對比驗證,固定順序,勿循環) */
 --s1:#178a50;--s2:#3b6fb5;--s3:#c46a1f;
}
[data-theme="dark"]{
 --bg:#0f1420;--card:#1a2030;--ink:#e8ecf4;--sub:#9aa3b2;--line:#2a3344;--accent:#5b8def;--accent2:#60a5fa;
 --tw:#34d399;--intl:#a78bfa;--warn:#f87171;--chip:#222b3d;--ok:#34d399;--bad:#f87171;
 --shadow:0 1px 3px rgba(0,0,0,.4);
 --s1:#2fa763;--s2:#4a82e0;--s3:#d17a20;
}
*{box-sizing:border-box}
html{font-size:17px}
body{margin:0;background:var(--bg);color:var(--ink);line-height:1.7;-webkit-text-size-adjust:100%;
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
.bigtext{font-size:1.05rem;background:var(--card);border:1px solid var(--line);border-radius:12px;padding:14px 16px;box-shadow:var(--shadow);margin-bottom:10px;line-height:1.8}
.big{font-size:1.02rem;line-height:1.85}.big li{margin:7px 0}.big2{font-size:.98rem;line-height:1.72}
#consult .card{margin-bottom:11px}#consult h3{font-size:1.02rem;margin:2px 0 10px}
.eli{background:#eff6ff;border-color:#bfdbfe}[data-theme="dark"] .eli{background:#10243f;border-color:#1e3a5f}
.flowwrap{display:flex;gap:18px;align-items:flex-start;flex-wrap:wrap}
.flowimg{flex:0 0 auto;background:#fbfcfe;border:1px solid var(--line);border-radius:10px;padding:6px}[data-theme="dark"] .flowimg{background:#0f1726}
.flowdesc{flex:1;min-width:240px}
.reflist .ref{padding:10px 0;border-bottom:1px solid var(--line)}.reflist .ref:last-child{border:0}
.rt{padding:10px 0;border-bottom:1px solid var(--line)}.rt:last-child{border:0}
.sev{display:inline-block;font-size:.72rem;font-weight:700;padding:2px 9px;border-radius:999px;color:#fff;margin-right:6px}
.sev.s1{background:#16a34a}.sev.s2{background:#65a30d}.sev.s3{background:#ca8a04}.sev.s4{background:#ea580c}.sev.s5{background:#dc2626}
.pricegrid{display:grid;grid-template-columns:repeat(auto-fit,minmax(210px,1fr));gap:10px;margin-bottom:11px}
.pcard2{background:var(--card);border:1px solid var(--line);border-radius:12px;padding:13px 15px;box-shadow:var(--shadow)}
.ptier{font-weight:800;color:var(--accent)}.pprice{font-size:1.15rem;font-weight:800;margin:4px 0}
@media(max-width:520px){.brand{font-size:1.1rem}}
/* ---- v5:動態流程圖/圖表動畫 ---- */
@keyframes nodeIn{from{opacity:0;transform:translateY(-8px)}to{opacity:1;transform:none}}
@keyframes edgeDraw{to{stroke-dashoffset:0}}
@keyframes barGrow{from{transform:scaleX(0)}to{transform:scaleX(1)}}
.anim .fnode{opacity:0;animation:nodeIn .5s ease forwards}
.anim .fedge{stroke-dasharray:400;stroke-dashoffset:400;animation:edgeDraw .6s ease forwards}
.anim .fbar{transform-origin:left center;animation:barGrow .8s ease forwards}
@media(prefers-reduced-motion:reduce){.anim .fnode,.anim .fedge,.anim .fbar{animation-duration:.01s}}
.replay{margin-top:6px;font-size:.85rem;padding:6px 12px;border:1px solid var(--line);background:var(--card);color:var(--accent);border-radius:8px;cursor:pointer;font-weight:700}
/* ---- v5:SWOT 縮放 ---- */
.zoomrow{display:flex;align-items:center;gap:10px;margin:6px 0}
.zoomrow input[type=range]{flex:1;max-width:260px}
#swotWrap{overflow:auto}
/* ---- v5:SPEC/報價單 ---- */
.spec-pros{color:var(--ok)}.spec-cons{color:var(--bad)}
.formula{font-family:ui-monospace,Menlo,monospace;background:var(--chip);border:1px solid var(--line);border-radius:10px;padding:10px 14px;font-size:1.02rem;display:inline-block;margin:6px 0}
.refnum{color:var(--accent);font-weight:700;text-decoration:none}
#quoteTbl input{padding:6px;border:1px solid var(--line);border-radius:8px;background:var(--card);color:var(--ink);width:100%;font-size:.92rem}
#quoteTbl td{vertical-align:middle}
.qtotal{font-size:1.15rem;font-weight:800;color:var(--accent);text-align:right;margin:8px 0}
.qbtns{display:flex;flex-wrap:wrap;gap:8px}
/* ---- v6:UI/UX 打磨 ---- */
:focus-visible{outline:3px solid var(--accent2);outline-offset:2px;border-radius:6px}
button,.btn,.chip,.filt,nav button{min-height:44px}
.daily{display:flex;gap:10px;align-items:flex-start;background:var(--chip);border:1px solid var(--line);border-radius:12px;padding:11px 14px;margin:8px 0;font-size:1rem}
.daily b{color:var(--accent)}
#stickyGo{display:none;position:fixed;left:12px;right:12px;bottom:12px;z-index:60;box-shadow:0 4px 14px rgba(0,0,0,.25)}
@media(max-width:640px){#stickyGo{display:block}}
/* ---- v6:動態簡報 ---- */
#deck{position:fixed;inset:0;z-index:100;background:var(--bg);display:none;flex-direction:column}
#deck.on{display:flex}
#deckTop{display:flex;justify-content:space-between;align-items:center;padding:10px 16px;border-bottom:1px solid var(--line)}
#deckSlide{flex:1;overflow:auto;padding:22px;max-width:900px;margin:0 auto;width:100%}
#deckSlide h1{font-size:1.9rem;color:var(--accent);margin:8px 0 14px}
#deckSlide .dbody{font-size:1.14rem;line-height:1.9}
#deckCtl{display:flex;gap:10px;align-items:center;justify-content:center;padding:12px;border-top:1px solid var(--line)}
.dot{width:11px;height:11px;border-radius:50%;background:var(--line);cursor:pointer}
.dot.on{background:var(--accent)}
.dslide{animation:nodeIn .5s ease}
.legend{display:flex;gap:16px;flex-wrap:wrap;margin:8px 0;font-size:.95rem}
.legend .sw{width:14px;height:14px;border-radius:4px;display:inline-block;margin-right:6px;vertical-align:-2px}
.schembox{background:var(--card);border:1px solid var(--line);border-radius:12px;padding:10px;text-align:center}
/* ---- v5:列印(報價單→PDF) ---- */
@media print{
 body *{visibility:hidden}
 #printArea,#printArea *{visibility:visible}
 #printArea{position:absolute;left:0;top:0;width:100%;background:#fff;color:#000}
 #printArea table{width:100%;border-collapse:collapse;font-size:12pt}
 #printArea th,#printArea td{border:1px solid #333;padding:6px 8px}
}
</style>
</head>
<body>
<div class="wrap">
 <header>
  <div class="brand"><span data-i18n="brand">🖥️ 二手電腦詢價系統</span><small data-i18n="brandSub">全球前10大平台比價・相容查詢・防詐客服</small></div>
  <div style="display:flex;gap:8px">
   <button class="theme" id="langBtn" title="中文／English" style="min-width:42px;font-weight:700">EN</button>
   <button class="theme" id="setBtn" title="AI 設定">⚙️</button>
   <button class="theme" id="themeBtn" title="深色／淺色">🌙</button>
  </div>
 </header>
 <div id="setPanel" class="card" style="display:none;margin:8px 0">
  <label class="fld" data-i18n="aiPanelLabel">AI 代理網址(Cloudflare Worker）— 留空則用規則式／手動版</label>
  <input type="text" id="aiUrl" placeholder="https://pcfinder-ai-proxy.xxx.workers.dev">
  <label class="fld" data-i18n="aiMemberLabel">會員碼 — AI 客服僅開放審核通過的會員(向站長申請)</label>
  <input type="text" id="aiMember" data-i18n-ph="aiMemberPh" placeholder="例:BRO-2026">
  <div class="searchrow" style="margin-top:8px">
   <button class="btn" id="aiSave" style="flex:1" data-i18n="aiSave">儲存</button>
   <button class="btn sec" id="aiTest" style="flex:1" data-i18n="aiTest">測試連線</button>
  </div>
  <div class="note" id="aiStatus"></div>
 </div>
 <nav id="nav">
  <button data-v="find" class="on" data-zh="🔎 詢價比價" data-en="🔎 Compare">🔎 詢價比價</button>
  <button data-v="sellers" data-zh="✅ 高評價賣家" data-en="✅ Top-rated">✅ 高評價賣家</button>
  <button data-v="compat" data-zh="🧩 規格相容" data-en="🧩 Compatibility">🧩 規格相容</button>
  <button data-v="photo" data-zh="📷 拍照找件" data-en="📷 Photo ID">📷 拍照找件</button>
  <button data-v="biz" data-zh="📊 商業分析" data-en="📊 Business">📊 商業分析</button>
  <button data-v="faq" data-zh="💬 FAQ客服" data-en="💬 FAQ">💬 FAQ客服</button>
  <button data-v="consult" data-zh="📑 顧問報告" data-en="📑 Consulting">📑 顧問報告</button>
  <button data-v="spec" data-zh="🧾 SPEC報價" data-en="🧾 SPEC & Quote">🧾 SPEC報價</button>
 </nav>

 <!-- 詢價 -->
 <section class="view on" id="find">
  <div class="searchrow">
   <input id="kw" type="search" data-i18n-ph="kwPh" placeholder="輸入型號或品名，例：i7-6700、H110M-K D3、MacBook Pro" autocomplete="off">
   <button class="btn" id="goAll" data-i18n="goAll">一鍵全開</button>
  </div>
  <div class="chips" id="cats"></div>
  <div class="chips" id="chips"></div>
  <div class="filters">
   <div class="filt on" data-region="all" data-i18n="fAll">全部</div>
   <div class="filt" data-region="tw" data-i18n="fTw">🇹🇼 台灣平台</div>
   <div class="filt" data-region="intl" data-i18n="fIntl">🌐 國際／整新</div>
  </div>
  <div class="tools">
   <label class="btn sec" style="text-align:center;cursor:pointer"><span data-i18n="loadLine">📂 載入 LINE 對話 txt 抓型號</span>
    <input type="file" id="lineFile" accept=".txt" hidden></label>
   <a class="btn sec" id="bmk" style="text-align:center" href="#" data-i18n-title="bmkTitle" data-i18n="bmk" title="拖到書籤列">⭐ 一鍵比價書籤（拖到書籤列）</a>
  </div>
  <div id="lineOut"></div>
  <div class="daily" id="daily"></div>
  <h2 data-i18n="hPlatforms">🏆 全球前 10 大二手電腦平台</h2>
  <div class="grid" id="platforms"></div>
  <div class="avoid" id="avoid"></div>
  <h2 data-i18n="hRules">🛡️ 防詐下單鐵則</h2>
  <div class="card panel"><ol id="rules"></ol></div>
  <h2 data-i18n="hTpl">📝 詢價範本</h2>
  <div class="card tpl"><button class="copy" id="copyBtn" data-i18n="copy">複製</button><pre id="tpl"></pre></div>
 </section>

 <!-- 高評價賣家 -->
 <section class="view" id="sellers">
  <h2 data-i18n="hSellers">✅ 高評價賣家直達（依露天評價數實查）</h2>
  <div class="note" data-i18n="sellersNote"></div>
  <div id="sellerList"></div>
  <h2 data-i18n="hPrice">📋 賣價對照表</h2>
  <div id="priceTables"></div>
 </section>

 <!-- 規格相容 -->
 <section class="view" id="compat">
  <h2 data-i18n="hCompat">🧩 零件相容性檢查</h2>
  <div class="card">
   <label class="fld" data-i18n="lCpu">CPU 處理器</label><select id="cCpu"></select>
   <label class="fld" data-i18n="lBoard">主機板</label><select id="cBoard"></select>
   <label class="fld" data-i18n="lRam">記憶體類型</label>
   <select id="cRam"><option value="" data-i18n="ramNone">（先不選）</option><option>DDR3</option><option>DDR3L</option><option>DDR4</option></select>
   <button class="btn" id="cGo" style="margin-top:12px;width:100%" data-i18n="checkCompat">檢查相容性</button>
   <div id="cResult"></div>
  </div>
  <h2 data-i18n="hCompare">📐 規格比較表</h2>
  <p class="muted" data-i18n="comparePick">勾選下方零件，產生規格比較表。</p>
  <button class="btn sec" id="cmpGo" data-i18n="genCompare">產生比較表</button>
  <div id="cmpOut"></div>
  <h3 data-i18n="h3Cpu">CPU 規格庫</h3><div class="tblscroll" id="cpuTbl"></div>
  <h3 data-i18n="h3Board">主機板規格庫</h3><div class="tblscroll" id="boardTbl"></div>
  <h3 data-i18n="h3Ram">記憶體規格</h3><div class="tblscroll" id="ramTbl"></div>
  <h2 data-i18n="hRules2">📏 相容性判斷規則</h2><div class="card panel"><ol id="partRules"></ol></div>
 </section>

 <!-- 拍照找件 -->
 <section class="view" id="photo">
  <h2 data-i18n="hPhoto">📷 拍照／上傳 找相容零件</h2>
  <div class="card camwrap">
   <div class="searchrow">
    <label class="btn sec" style="flex:1;text-align:center;cursor:pointer"><span data-i18n="upload">🖼️ 上傳照片</span>
     <input type="file" id="upPhoto" accept="image/*" capture="environment" hidden></label>
    <button class="btn sec" id="camBtn" style="flex:1" data-i18n="openCam">📸 開啟相機</button>
   </div>
   <video id="cam" autoplay playsinline style="display:none"></video>
   <button class="btn" id="shotBtn" style="display:none" data-i18n="shoot">拍照</button>
   <canvas id="shot" style="display:none"></canvas>
   <img id="photo" style="display:none" alt="預覽">
   <label class="fld" data-i18n="photoModelLabel">輸入照片上看到的型號（晶片/主板絲印），自動查相容＋比價</label>
   <input type="text" id="photoModel" data-i18n-ph="photoModelPh" placeholder="例：i7-6700、H110M-K D3、DDR3L 8G">
   <div class="searchrow" style="margin-top:8px">
    <button class="btn" id="photoFind" style="flex:1" data-i18n="photoFind">🔎 拿去比價</button>
    <a class="btn sec" id="lens" style="flex:1;text-align:center" target="_blank" rel="noopener" href="https://lens.google.com/" data-i18n="lens">🔍 Google Lens 以圖搜尋</a>
   </div>
   <button class="btn" id="aiVision" style="margin-top:8px" data-i18n="aiVision">🤖 AI 辨識這張照片（需設定 AI)</button>
   <div id="visionOut"></div>
   <div class="note" data-i18n-html="photoNote">⚠️ 誠實說明：純靜態網站<b>無法自動辨識</b>照片裡的晶片（那需要 AI 後端）。這裡做的是「拍照／上傳留存 ＋ 你輸入型號 → 自動查相容性＋一鍵比價」，並可用 Google Lens 以圖搜尋型號。要真‧自動辨識可再接 AI API（升級項）。</div>
  </div>
 </section>

 <!-- 商業分析 -->
 <section class="view" id="biz">
  <div class="card" style="margin-bottom:6px">
   <label class="fld" data-i18n="bizLabel">分析標的(預設「本系統」;輸入任意公司／產品,需設定 AI 才會動態產生)</label>
   <div class="searchrow">
    <input type="text" id="bizTopic" data-i18n-ph="bizTopicPh" placeholder="例:二手筆電回收事業、某新創 App">
    <button class="btn" id="bizGen" data-i18n="bizGen">動態產生</button>
   </div>
   <button class="btn sec" id="pptBtn" style="margin-top:8px;width:100%" data-i18n="pptBtn">⬇️ 下載 PPT（封面＋五力＋BMC＋SWOT）</button>
   <div class="note" id="bizNote"></div>
  </div>
  <h2 id="bizTitle" data-i18n="bizTitle">📊 波特五力分析（本系統）</h2>
  <div class="card radarbox"><div id="radar"></div><div id="forceList" style="flex:1;min-width:260px"></div></div>
  <h2 data-i18n="hBmc">🧱 商業模式圖 BMC</h2>
  <div class="bmc" id="bmc"></div>
  <h2 data-i18n="hSwot">🎯 SWOT 分析</h2>
  <div class="zoomrow"><span data-i18n="zoomLbl">縮放</span><input type="range" id="swotZoom" min="50" max="150" value="100" step="10"><span id="swotZoomVal">100%</span></div>
  <div id="swotWrap"><div class="swot" id="swot"></div></div>
 </section>

 <!-- SPEC 報價 -->
 <section class="view" id="spec">
  <h2 data-i18n="hSpec">🧾 各廠商完整 SPEC 與比價報告</h2>
  <button class="btn" id="deckOpen" style="width:100%;margin-bottom:10px" data-i18n="deckOpen">🎬 播放動態簡報(SPEC 比價・雷達・自動播放)</button>
  <div id="specBody"></div>
  <h2 data-i18n="hQuote">🧮 報價單(可匯出/匯入)</h2>
  <div class="card">
   <div class="qbtns">
    <button class="btn" id="qAdd" data-i18n="qAdd">＋ 新增一列</button>
    <button class="btn sec" id="qXls" data-i18n="qXls">⬇️ 匯出 XLS</button>
    <button class="btn sec" id="qPdf" data-i18n="qPdf">🖨 匯出 PDF(列印)</button>
    <label class="btn sec" style="cursor:pointer"><span data-i18n="qImp">⬆️ 匯入 XLS</span><input type="file" id="qImport" accept=".xlsx,.xls" hidden></label>
   </div>
   <div class="tblscroll" style="margin-top:10px"><table id="quoteTbl"><thead></thead><tbody></tbody></table></div>
   <div class="qtotal" id="qTotal"></div>
   <div class="note" data-i18n="qNote">匯出 XLS 可在 Excel 開啟編輯,之後可再「匯入」回本頁繼續;PDF 走系統列印(選「儲存為 PDF」)。</div>
  </div>
 </section>
 <div id="printArea" style="display:none"></div>
 <button class="btn" id="stickyGo" data-i18n="goAll">一鍵全開</button>
 <div id="deck" role="dialog" aria-modal="true">
  <div id="deckTop"><b id="deckTitle"></b>
   <div style="display:flex;gap:8px">
    <button class="replay" id="deckAuto">▶</button>
    <button class="replay" id="deckClose">✕</button>
   </div></div>
  <div id="deckSlide"></div>
  <div id="deckCtl">
   <button class="replay" id="deckPrev">←</button>
   <div id="deckDots" style="display:flex;gap:8px"></div>
   <button class="replay" id="deckNext">→</button>
  </div>
 </div>

 <!-- FAQ -->
 <section class="view" id="faq">
  <h2 data-i18n="hFaq">💬 規則式 FAQ 客服</h2>
  <div class="note" data-i18n-html="faqNote">問「DDR3L 能用嗎」「賣家叫我取消」「嗶兩聲沒畫面」等都行。<b>未設定 AI</b> 時用本專案知識庫的關鍵字比對;<b>設定 AI 後</b>(右上 ⚙️)升級成真 AI 客服。</div>
  <div class="faqchat" style="margin-top:10px">
   <div id="chatlog"></div>
   <div class="searchrow" style="margin-top:8px">
    <input id="askIn" type="text" data-i18n-ph="askPh" placeholder="輸入你的問題…">
    <button class="btn" id="askBtn" data-i18n="ask">問</button>
   </div>
  </div>
  <h2 data-i18n="hFaqList">📚 常見問題（點開看答案）</h2>
  <div id="faqList"></div>
 </section>

 <!-- 顧問報告 Consulting -->
 <section class="view" id="consult">
  <div class="bigtext" id="cIntro"></div>
  <h2 id="cH_guide"></h2><div id="cGuide"></div>
  <h2 id="cH_flows"></h2><div id="cFlows"></div>
  <h2 id="cH_market"></h2><div id="cMarket"></div>
  <h2 id="cH_critique"></h2><div id="cCritique"></div>
  <h2 id="cH_money"></h2><div id="cMoney"></div>
 </section>

 <footer id="foot"></footer>
</div>

<script src="libs/pptxgen.bundle.js"></script>
<script src="libs/xlsx.full.min.js"></script>
<script>
const APP = /*__APP_DATA__*/;
const $=s=>document.querySelector(s), $$=s=>[...document.querySelectorAll(s)];
const enc=s=>encodeURIComponent((s||"").trim());
const esc=s=>(s||"").replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;");
let region="all";
let lastPhotoB64=null,lastPhotoMime="image/jpeg";

/* ---------- AI 代理 (選配,會員審核) ---------- */
function aiEndpoint(){try{return localStorage.getItem("pcf-ai")||""}catch(e){return ""}}
function memberCode(){try{return localStorage.getItem("pcf-member")||""}catch(e){return ""}}
async function callAI(payload){const url=aiEndpoint();if(!url)throw new Error("未設定 AI 代理網址");
 payload=Object.assign({member_code:memberCode()},payload);
 const r=await fetch(url,{method:"POST",headers:{"content-type":"application/json"},body:JSON.stringify(payload)});
 const d=await r.json().catch(()=>({}));
 if(!r.ok){if(d.error==="member_required")throw new Error(ui("memberErr"));throw new Error(d.error||("HTTP "+r.status));}
 return d;}
function refreshAIStatus(){const on=!!aiEndpoint();const s=$("#aiStatus");
 if(s)s.innerHTML=on?(ui("aiOn")+(memberCode()?"":("<br>"+ui("memberMiss")))):ui("aiOff");}

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
  const rt=p.region==="tw"?'<span class="tag tw">'+ui("tagTw")+'</span>':'<span class="tag intl">'+ui("tagIntl")+'</span>';
  const href=k?purl(p,k):"#",cls=k?"pgo":"pgo disabled",lab=k?(lang==="zh"?("在此搜尋「"+esc(k)+"」 →"):("Search “"+esc(k)+"” →")):ui("needKw");
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
   '<a class="sgo" target="_blank" rel="noopener" href="https://www.ruten.com.tw/store/'+esc(s.account)+'/">'+ui("gotoStore")+'</a>';
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
  let html='<div class="verdict '+(r.ok?"ok":"bad")+'"><b>'+(r.ok?ui("verdictOk"):ui("verdictBad"))+'</b>';
  if(r.reasons.length)html+='<ul>'+r.reasons.map(x=>"<li>"+esc(x)+"</li>").join("")+'</ul>';
  if(r.warn.length)html+='<ul>'+r.warn.map(x=>"<li>⚠ "+esc(x)+"</li>").join("")+'</ul>';
  html+='</div>';$("#cResult").innerHTML=html;
 };
 // tables with compare checkboxes
 $("#cpuTbl").innerHTML=tbl((UI[lang]||UI.zh).thCpu,
  APP.parts.cpus.map((c,i)=>['<input type="checkbox" data-t="cpu" data-i="'+i+'">',c.model,c.socket,c.gen||"",c.cores_threads,c.tdp,c.mem_support]));
 $("#boardTbl").innerHTML=tbl((UI[lang]||UI.zh).thBoard,
  APP.parts.boards.map((b,i)=>['<input type="checkbox" data-t="board" data-i="'+i+'">',b.model,b.socket,b.chipset,b.mem_type,b.mem_slots||"",b.max_mem||"",b.form_factor||""]));
 $("#ramTbl").innerHTML=tbl((UI[lang]||UI.zh).thRam,APP.parts.ram.map(r=>[r.type,r.voltage,r.slot||"",r.note]));
 $("#partRules").innerHTML=APP.parts.rules.map(r=>"<li>"+esc(r)+"</li>").join("");
}
function tbl(head,rows){
 return '<table><thead><tr>'+head.map(h=>"<th>"+esc(h)+"</th>").join("")+'</tr></thead><tbody>'+
  rows.map(r=>"<tr>"+r.map((c)=>"<td>"+(/^<(input|a |button)/.test(String(c))?c:esc(String(c)))+"</td>").join("")+"</tr>").join("")+'</tbody></table>';
}
$("#cmpGo").onclick=()=>{
 const picks=$$("#compat input[type=checkbox]:checked").map(c=>({t:c.dataset.t,i:+c.dataset.i}));
 if(!picks.length){$("#cmpOut").innerHTML='<div class="note">先在下面勾選要比較的零件。</div>';return;}
 const rows=picks.map(p=>{const x=p.t==="cpu"?APP.parts.cpus[p.i]:APP.parts.boards[p.i];
  return p.t==="cpu"?[x.model,"CPU",x.socket,x.gen||"",x.cores_threads,x.tdp,x.mem_support,x.note||""]
   :[x.model,"主機板",x.socket,x.chipset,x.form_factor||"",x.max_mem||"",x.mem_type,x.note||""];});
 $("#cmpOut").innerHTML='<div class="tblscroll">'+tbl((UI[lang]||UI.zh).thCmp,rows)+'</div>';
 $("#cmpOut").scrollIntoView({block:"start"});
};

/* ---------- 拍照 ---------- */
let stream=null;
$("#upPhoto").addEventListener("change",e=>{const f=e.target.files[0];if(!f)return;
 const img=$("#photo");img.src=URL.createObjectURL(f);img.style.display="block";
 const r=new FileReader();r.onload=()=>{const m=String(r.result).match(/^data:([^;]+);base64,(.*)$/);if(m){lastPhotoMime=m[1];lastPhotoB64=m[2];}};r.readAsDataURL(f);});
$("#camBtn").onclick=async()=>{
 try{stream=await navigator.mediaDevices.getUserMedia({video:{facingMode:"environment"}});
  const v=$("#cam");v.srcObject=stream;v.style.display="block";$("#shotBtn").style.display="block";
 }catch(e){alert("無法開啟相機："+e.message+"\n可改用『上傳照片』。");}
};
$("#shotBtn").onclick=()=>{const v=$("#cam"),cv=$("#shot");cv.width=v.videoWidth;cv.height=v.videoHeight;
 cv.getContext("2d").drawImage(v,0,0);const img=$("#photo");const du=cv.toDataURL("image/jpeg",.9);img.src=du;img.style.display="block";lastPhotoMime="image/jpeg";lastPhotoB64=du.split(",")[1];
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
 $("#chips").innerHTML='<span class="muted" style="align-self:center">'+ui("common")+'</span>'+APP.quick.map(k=>'<span class="chip" data-k="'+esc(k)+'">'+esc(k)+'</span>').join("");
 $("#chips").querySelectorAll(".chip").forEach(c=>c.onclick=()=>{setKw(c.dataset.k);$("#kw").focus();});
 $("#rules").innerHTML=APP.rules.map(r=>"<li>"+r+"</li>").join("");
 $("#tpl").textContent=APP.template;
 $("#avoid").innerHTML="🚫 <b>避雷：</b>"+esc(APP.avoid);
 $("#foot").innerHTML=ui("footer").replace("{date}",APP.date);
}
$("#copyBtn").onclick=async()=>{try{await navigator.clipboard.writeText(APP.template);
 const b=$("#copyBtn");b.textContent="已複製 ✓";b.classList.add("done");setTimeout(()=>{b.textContent="複製";b.classList.remove("done");},1800);
}catch(e){alert("複製失敗，請手動選取。");}};

/* ---------- v5:SPEC 比價報告 ---------- */
function offLink(model,kind){const Lk=(APP.research||{}).links||{};const arr=Lk[kind]||[];
 const norm=s=>String(s||"").toLowerCase().replace(/[^a-z0-9]/g,"");
 const nm=norm(model);
 const hit=arr.find(x=>{const nx=norm(x.model);if(nx&&(nm.includes(nx)||nx.includes(nm)))return true;
  return String(x.model||"").split(/[\s()（）,、]+/).some(t=>{const nt=norm(t);return nt.length>=5&&/\d/.test(nt)&&nm.includes(nt);});});
 const url=hit&&(hit.official_url||hit.ark_url);
 return url?'<a href="'+esc(url)+'" target="_blank" rel="noopener" title="'+esc((hit.note&&L(hit.note))||"official")+'">📷</a>':"—";}
function renderSpec(){const S=(APP.research||{}).spec;const host=$("#specBody");if(!host)return;
 if(!S){host.innerHTML='<div class="note">尚無 SPEC 報告資料。</div>';renderQuote();return;}
 let n=0;const T=(UI[lang]||UI.zh);
 host.innerHTML=
  '<div class="bigtext">'+esc(L(S.intro))+'</div>'+
  '<div class="card"><b>'+ui("formulaH")+'：'+esc(L(S.formula.name))+'</b><div class="formula">'+esc(S.formula.expr)+'</div><div class="big2">'+esc(L(S.formula.vars))+'<br>'+esc(L(S.formula.explain))+'</div></div>'+
  '<div class="card"><b>'+(lang==="zh"?"主機板 SPEC(LGA1151・DDR3/DDR3L)":"Motherboard SPEC (LGA1151 · DDR3/DDR3L)")+'</b><div class="tblscroll">'+
   tbl(T.thBoards.concat([ui("official")]),(S.boards||[]).map(b=>[b.brand,b.model,b.socket,b.chipset,b.memory,b.form,L(b.io),b.price,L(b.pros),L(b.cons),offLink(b.model,"boards")]))+'</div></div>'+
  '<div class="note">'+ui("photoHint")+'</div>'+
  '<div class="card"><b>'+(lang==="zh"?"CPU 行情與 CP 值":"CPU used prices & value")+'</b><div class="tblscroll">'+
   tbl(T.thCpus2.concat([ui("official")]),(S.cpus||[]).map(c=>[c.model,c.cores,c.clock,c.tdp,c.price,L(c.value_note),offLink(c.model,"cpus")]))+'</div></div>'+
  (S.related||[]).map(cat=>'<div class="card"><b>'+esc(L(cat.category))+'</b><div class="tblscroll">'+
   tbl(T.thRel,(cat.items||[]).map(i=>[i.model,L(i.key_spec),i.price,L(i.note)]))+'</div></div>').join("")+
  '<div class="card anim" id="sChart"><b>'+esc(L(S.chart.title))+'</b>'+barChart(S.chart.bars)+'<div class="note">'+esc(L(S.chart.caption))+'</div><button class="replay" data-rp="#sChart">'+ui("flowReplay")+'</button></div>'+
  '<div class="card"><b>'+ui("compH")+'</b><ul class="big2">'+(S.comparison||[]).map(x=>"<li>"+esc(L(x))+"</li>").join("")+'</ul></div>'+
  '<div class="card"><b>'+ui("refsH")+'</b><div class="reflist">'+(S.references||[]).map(r=>refItem(r,++n)).join("")+'</div></div>';
 $$("#specBody .replay").forEach(b=>b.onclick=()=>animate(b.dataset.rp));
 renderQuote();}

/* ---------- v6:每日動態輪播 ---------- */
function renderDaily(){const el=$("#daily");if(!el)return;const R=APP.research||{};
 const tips=((R.tips||{}).tips)||[];const day=Math.floor(Date.now()/864e5);
 const tip=tips.length?L(tips[day%tips.length]):"";
 const kw=APP.quick[day%APP.quick.length];
 el.innerHTML="<div>📅 <b>"+new Date().toISOString().slice(0,10)+"</b><br><b>"+ui("dailyTip")+"</b>："+esc(tip)+
  "<br><b>"+ui("dailyPick")+"</b>：<span class=\"chip\" id=\"dailyKw\">"+esc(kw)+"</span></div>";
 const c=$("#dailyKw");if(c)c.onclick=()=>{setKw(kw);$("#kw").focus();};}

/* ---------- v6:雷達圖(類別色已驗證,固定順序) ---------- */
function radarSVG(dims,series){const n=dims.length,cx=170,cy=160,R=110;
 const pt=(i,v)=>{const a=-Math.PI/2+i*2*Math.PI/n;const r=R*v/5;return[cx+r*Math.cos(a),cy+r*Math.sin(a)];};
 let g="";
 for(let ring=1;ring<=5;ring++){const pts=dims.map((_,i)=>pt(i,ring).join(",")).join(" ");
  g+='<polygon points="'+pts+'" fill="none" stroke="var(--line)" stroke-width="1"/>';}
 dims.forEach((d,i)=>{const e=pt(i,5);g+='<line x1="'+cx+'" y1="'+cy+'" x2="'+e[0]+'" y2="'+e[1]+'" stroke="var(--line)"/>';
  const lp=pt(i,5.85);g+='<text x="'+lp[0]+'" y="'+(lp[1]+4)+'" font-size="12.5" text-anchor="middle" fill="var(--ink)">'+esc(L(d))+'</text>';});
 series.forEach((s,si)=>{const col="var(--s"+(si+1)+")";const pts=s.values.map((v,i)=>pt(i,v).join(",")).join(" ");
  g+='<polygon class="fnode" style="animation-delay:'+(si*0.35)+'s" points="'+pts+'" fill="'+col+'" fill-opacity="0.13" stroke="'+col+'" stroke-width="2"/>';
  s.values.forEach((v,i)=>{const p=pt(i,v);g+='<circle class="fnode" style="animation-delay:'+(si*0.35)+'s" cx="'+p[0]+'" cy="'+p[1]+'" r="4" fill="'+col+'"/>';});});
 return '<svg viewBox="0 0 340 330" width="100%" style="max-width:430px">'+g+'</svg>';}
function radarLegend(series){return '<div class="legend">'+series.map((s,i)=>'<span><span class="sw" style="background:var(--s'+(i+1)+')"></span>'+esc(L(s.name))+'</span>').join("")+'</div>';}
function radarTable(dims,series){return '<div class="tblscroll">'+tbl([""].concat(dims.map(d=>L(d))),series.map(s=>[L(s.name)].concat(s.values.map(String))))+'</div>';}

/* ---------- v6:主機板示意圖(自繪,非實照) ---------- */
function schemSVG(){return '<svg viewBox="0 0 300 210" width="100%" style="max-width:360px">'+
 '<rect x="10" y="10" width="280" height="190" rx="8" fill="#2e7d4f22" stroke="var(--accent)" stroke-width="2"/>'+
 '<rect x="40" y="40" width="70" height="70" fill="var(--card)" stroke="var(--ink)"/><text x="75" y="80" font-size="11" text-anchor="middle" fill="var(--ink)">LGA1151</text>'+
 '<rect x="140" y="30" width="14" height="110" fill="var(--s2)" fill-opacity=".5" stroke="var(--s2)"/><rect x="162" y="30" width="14" height="110" fill="var(--s2)" fill-opacity=".5" stroke="var(--s2)"/>'+
 '<text x="158" y="155" font-size="10" text-anchor="middle" fill="var(--ink)">DDR3/DDR3L ×2</text>'+
 '<rect x="40" y="160" width="150" height="12" fill="var(--s3)" fill-opacity=".5" stroke="var(--s3)"/><text x="115" y="188" font-size="10" text-anchor="middle" fill="var(--ink)">PCIe ×16</text>'+
 '<rect x="230" y="40" width="40" height="90" fill="var(--chip)" stroke="var(--sub)"/><text x="250" y="150" font-size="9" text-anchor="middle" fill="var(--sub)">I/O</text></svg>';}

/* ---------- v6:動態簡報 ---------- */
let deckIdx=0,deckTimer=null;
function deckSlides(){const R=APP.research||{},S=R.spec||{},D=R.deck||{},C=APP.consult||{};
 const sl=(D.slides||[]);const get=k=>sl.find(s=>s.key===k)||{title:{zh:k,en:k},body:{zh:"",en:""}};
 const T=(UI[lang]||UI.zh);
 return [
  {t:get("cover"),html:'<div class="schembox">'+schemSVG()+'<div class="muted">'+ui("schemNote")+'</div></div><div class="muted" style="margin-top:8px">'+APP.date+"　·　"+(lang==="zh"?"顧問級動態簡報":"Consultant dynamic deck")+"</div>"},
  {t:get("market"),html:(C.market?'<div class="anim">'+barChart(C.market.chart.bars)+'</div><div class="note">'+esc(L(C.market.chart.caption))+'</div>':"")},
  {t:get("boards"),html:'<div class="tblscroll">'+tbl(T.thBoards.slice(0,8),(S.boards||[]).slice(0,7).map(b=>[b.brand,b.model,b.socket,b.chipset,b.memory,b.form,L(b.io),b.price]))+'</div>'},
  {t:get("radar"),html:(D.radar?('<div class="anim">'+radarSVG(D.radar.dims,D.radar.series)+'</div>'+radarLegend(D.radar.series)+radarTable(D.radar.dims,D.radar.series)+'<div class="note">'+esc(L(D.radar.method))+'</div>'):"")},
  {t:get("price"),html:(S.chart?'<div class="anim">'+barChart(S.chart.bars)+'</div><div class="note">'+esc(L(S.chart.caption))+'</div>':"")},
  {t:get("proscons"),html:'<ul class="big2">'+((S.comparison||[]).map(x=>"<li>"+esc(L(x))+"</li>").join(""))+'</ul>'},
  {t:get("action"),html:(D.honest?'<div class="note"><b>Truth</b><ul class="big2">'+D.honest.map(h=>"<li>"+esc(L(h))+"</li>").join("")+'</ul></div>':"")},
 ];}
function deckShow(i){const s=deckSlides();deckIdx=(i+s.length)%s.length;const cur=s[deckIdx];
 $("#deckTitle").textContent=(deckIdx+1)+"/"+s.length+"　"+L(cur.t.title);
 $("#deckSlide").innerHTML='<div class="dslide"><h1>'+esc(L(cur.t.title))+'</h1><div class="dbody">'+esc(L(cur.t.body)).replace(/\n/g,"<br>")+'</div><div style="margin-top:14px">'+cur.html+'</div></div>';
 $("#deckDots").innerHTML=s.map((_,j)=>'<span class="dot'+(j===deckIdx?" on":"")+'" data-j="'+j+'"></span>').join("");
 $$("#deckDots .dot").forEach(d=>d.onclick=()=>deckShow(+d.dataset.j));}
function deckStop(){if(deckTimer){clearInterval(deckTimer);deckTimer=null;$("#deckAuto").textContent="▶";}}
$("#deckOpen").onclick=()=>{$("#deck").classList.add("on");deckShow(0);};
$("#deckClose").onclick=()=>{deckStop();$("#deck").classList.remove("on");};
$("#deckPrev").onclick=()=>deckShow(deckIdx-1);
$("#deckNext").onclick=()=>deckShow(deckIdx+1);
$("#deckAuto").onclick=()=>{if(deckTimer){deckStop();}else{deckTimer=setInterval(()=>deckShow(deckIdx+1),6000);$("#deckAuto").textContent="⏸";}};
document.addEventListener("keydown",e=>{if(!$("#deck").classList.contains("on"))return;
 if(e.key==="Escape"){deckStop();$("#deck").classList.remove("on");}
 if(e.key==="ArrowRight")deckShow(deckIdx+1);if(e.key==="ArrowLeft")deckShow(deckIdx-1);});
$("#stickyGo").onclick=()=>{ $$("#nav button").forEach(x=>x.classList.remove("on"));$('#nav button[data-v=find]').classList.add("on");
 $$(".view").forEach(v=>v.classList.remove("on"));$("#find").classList.add("on");window.scrollTo(0,0);$("#kw").focus();};

/* ---------- v5:報價單(匯出/匯入) ---------- */
let qRows=[
 {item:"ASUS H110M-K D3",spec:"LGA1151 / DDR3L",qty:1,price:1000,seller:"js3c0800(露天)",note:"D3版,非D4"},
 {item:"Intel i7-6700",spec:"4C8T / LGA1151",qty:1,price:1800,seller:"露天",note:"含風扇"},
 {item:"DDR3L-1600 8GB",spec:"1.35V",qty:2,price:250,seller:"露天",note:""},
];
function qTotal(){return qRows.reduce((s,r)=>s+(Number(r.qty)||0)*(Number(r.price)||0),0);}
function renderQuote(){const T=(UI[lang]||UI.zh);const thead=$("#quoteTbl thead"),tbody=$("#quoteTbl tbody");if(!thead)return;
 thead.innerHTML="<tr>"+T.qth.map(h=>"<th>"+esc(h)+"</th>").join("")+"</tr>";
 tbody.innerHTML=qRows.map((r,i)=>"<tr>"+
  ['item','spec','qty','price'].map(k=>'<td'+(k==='qty'||k==='price'?' style="max-width:90px"':'')+'><input data-i="'+i+'" data-k="'+k+'" value="'+esc(String(r[k]??""))+'"'+(k==='qty'||k==='price'?' type="number" min="0"':'')+'></td>').join("")+
  '<td style="text-align:right;font-weight:700">'+((Number(r.qty)||0)*(Number(r.price)||0)).toLocaleString()+'</td>'+
  ['seller','note'].map(k=>'<td><input data-i="'+i+'" data-k="'+k+'" value="'+esc(String(r[k]??""))+'"></td>').join("")+
  '<td><button class="replay" data-del="'+i+'">'+ui("delRow")+'</button></td></tr>').join("");
 $("#qTotal").textContent=ui("qTotalLbl")+" "+qTotal().toLocaleString();
 tbody.querySelectorAll("input").forEach(inp=>inp.onchange=()=>{qRows[+inp.dataset.i][inp.dataset.k]=inp.value;renderQuote();});
 tbody.querySelectorAll("[data-del]").forEach(b=>b.onclick=()=>{qRows.splice(+b.dataset.del,1);renderQuote();});}
$("#qAdd").onclick=()=>{qRows.push({item:"",spec:"",qty:1,price:0,seller:"",note:""});renderQuote();};
$("#qXls").onclick=()=>{const T=(UI[lang]||UI.zh);
 const aoa=[[T.qTitle],[ui("qTotalLbl"),qTotal()],[],T.qth.slice(0,7)]
  .concat(qRows.map(r=>[r.item,r.spec,Number(r.qty)||0,Number(r.price)||0,(Number(r.qty)||0)*(Number(r.price)||0),r.seller,r.note]));
 const ws=XLSX.utils.aoa_to_sheet(aoa);ws["!cols"]=[{wch:22},{wch:18},{wch:6},{wch:10},{wch:10},{wch:18},{wch:18}];
 const wb=XLSX.utils.book_new();XLSX.utils.book_append_sheet(wb,ws,lang==="zh"?"報價單":"Quote");
 XLSX.writeFile(wb,(lang==="zh"?"報價單_":"quote_")+APP.date+".xlsx");};
$("#qImport").addEventListener("change",e=>{const f=e.target.files[0];if(!f)return;const rd=new FileReader();
 rd.onload=()=>{try{const wb=XLSX.read(rd.result,{type:"array"});const ws=wb.Sheets[wb.SheetNames[0]];
  const aoa=XLSX.utils.sheet_to_json(ws,{header:1});
  const hi=aoa.findIndex(row=>row&&row.length>=4&&String(row[2]||"").match(/數量|Qty/i));
  const body=aoa.slice(hi>=0?hi+1:0).filter(r=>r&&(r[0]||r[1]));
  qRows=body.map(r=>({item:String(r[0]??""),spec:String(r[1]??""),qty:Number(r[2])||0,price:Number(r[3])||0,seller:String(r[5]??""),note:String(r[6]??"")}));
  renderQuote();}catch(err){alert((lang==="zh"?"匯入失敗:":"Import failed: ")+err.message);}e.target.value="";};
 rd.readAsArrayBuffer(f);});
$("#qPdf").onclick=()=>{const T=(UI[lang]||UI.zh);const pa=$("#printArea");
 pa.innerHTML="<h2>"+esc(T.qTitle)+"</h2><div>"+APP.date+"</div><table><tr>"+T.qth.slice(0,7).map(h=>"<th>"+esc(h)+"</th>").join("")+"</tr>"+
  qRows.map(r=>"<tr>"+[r.item,r.spec,r.qty,r.price,(Number(r.qty)||0)*(Number(r.price)||0),r.seller,r.note].map(c=>"<td>"+esc(String(c??""))+"</td>").join("")+"</tr>").join("")+
  '<tr><td colspan="4" style="text-align:right;font-weight:bold">'+ui("qTotalLbl")+'</td><td style="font-weight:bold">'+qTotal().toLocaleString()+"</td><td></td><td></td></tr></table>";
 pa.style.display="block";window.print();setTimeout(()=>{pa.style.display="none";},400);};

/* ---------- v5:SWOT 縮放 ---------- */
$("#swotZoom").addEventListener("input",e=>{const v=+e.target.value;$("#swotZoomVal").textContent=v+"%";
 const s=$("#swot");s.style.zoom=v/100;if(getComputedStyle(s).zoom==="1"&&v!==100){s.style.transformOrigin="top left";s.style.transform="scale("+(v/100)+")";}else if(v===100){s.style.transform="";}});

/* ---------- 設定面板 ---------- */
let bizTopicName="本系統";
$("#setBtn").onclick=()=>{const p=$("#setPanel");const open=p.style.display==="none";p.style.display=open?"block":"none";if(open){$("#aiUrl").value=aiEndpoint();$("#aiMember").value=memberCode();}};
$("#aiSave").onclick=()=>{try{localStorage.setItem("pcf-ai",$("#aiUrl").value.trim());localStorage.setItem("pcf-member",$("#aiMember").value.trim());}catch(e){}refreshAIStatus();};
$("#aiTest").onclick=async()=>{const s=$("#aiStatus");s.textContent="測試中…";try{const d=await callAI({mode:"chat",messages:[{role:"user",content:"測試:H110M-K D3 能用 DDR3L 嗎?一句話"}]});s.textContent="✅ 連線成功:"+String(d.reply||"").slice(0,50);}catch(e){s.textContent="❌ 失敗:"+e.message;}};

/* ---------- FAQ:真 AI 優先,否則規則式 ---------- */
const chatHist=[];
$("#askBtn").onclick=async()=>{const q=$("#askIn").value.trim();if(!q)return;chat("me",q);$("#askIn").value="";
 if(aiEndpoint()){chatHist.push({role:"user",content:q});chat("bot",ui("thinking"));const ph=$("#chatlog").lastChild;
  try{const d=await callAI({mode:"chat",messages:chatHist});const a=d.reply||"(無回覆)";ph.textContent="🤖 "+a;chatHist.push({role:"assistant",content:a});}
  catch(e){const m=matchFaq(q);const pre=e.message+"\n\n";
   ph.textContent=m?(pre+(lang==="zh"?"改用內建知識庫回答:":"Rule-based answer instead:")+"\n【"+m.q+"】\n"+m.a):(pre+(lang==="zh"?"知識庫也無對應答案。":"No rule-based match either."));}
  return;}
 const m=matchFaq(q);chat("bot",m?("【"+m.q+"】\n"+m.a):"知識庫沒有直接答案。可在右上 ⚙️ 設定 AI 升級成真客服,或往下看常見問題。");};

/* ---------- 拍照 AI 辨識 ---------- */
$("#aiVision").onclick=async()=>{const out=$("#visionOut");
 if(!aiEndpoint()){out.innerHTML='<div class="note">請先在右上 ⚙️ 設定 AI 代理網址。</div>';return;}
 if(!lastPhotoB64){out.innerHTML='<div class="note">請先「上傳照片」或「拍照」。</div>';return;}
 out.innerHTML='<div class="note">🤖 AI 辨識中…</div>';
 try{const d=await callAI({mode:"vision",image:lastPhotoB64,media_type:lastPhotoMime});const r=d.result;
  if(!r){out.innerHTML='<div class="note">AI 回覆無法解析:'+esc(String(d.raw||"").slice(0,120))+'</div>';return;}
  const rows=[["腳位",r.socket],["記憶體",r.memory_type],["規格",r.key_specs],["相容",r.compatibility_note],["信心",r.confidence]].filter(x=>x[1]);
  out.innerHTML='<div class="verdict ok"><b>'+esc((r.category||"零件")+"："+(r.brand||"")+" "+(r.model||""))+'</b><ul>'+rows.map(x=>"<li>"+esc(x[0])+"："+esc(x[1])+"</li>").join("")+(r.caveat?"<li>⚠ "+esc(r.caveat)+"</li>":"")+'</ul></div>';
  if(r.model)$("#photoModel").value=((r.brand||"")+" "+r.model).trim();
 }catch(e){out.innerHTML='<div class="note">❌ '+esc(e.message)+'</div>';}};

/* ---------- 商業分析:動態產生 ---------- */
$("#bizGen").onclick=async()=>{const t=$("#bizTopic").value.trim(),note=$("#bizNote");
 if(!t){note.textContent="輸入標的後再產生。";return;}
 if(!aiEndpoint()){note.textContent="動態產生需先設定 AI(右上 ⚙️)。未設定時顯示的是本系統的內建分析。";return;}
 note.textContent="🤖 產生中…(約 10–30 秒)";
 try{const d=await callAI({mode:"analysis",topic:t});const a=d.analysis;
  if(!a){note.textContent="AI 回覆無法解析,稍後再試。";return;}
  if(a.fiveForces)APP.fiveForces=a.fiveForces;if(a.bmc)APP.bmc=a.bmc;if(a.swot)APP.swot=a.swot;
  bizTopicName=a.topic||t;$("#bizTitle").textContent="📊 波特五力分析（"+bizTopicName+"）";renderBiz();
  note.textContent="✅ 已產生「"+bizTopicName+"」的分析,可下載 PPT。";
 }catch(e){note.textContent="❌ "+e.message;}};

/* ---------- 下載 PPT ---------- */
$("#pptBtn").onclick=()=>{
 if(typeof PptxGenJS==="undefined"){alert("PPT 套件還在載入,請稍候再按一次。");return;}
 const p=new PptxGenJS();
 let s=p.addSlide();s.background={color:"F4F6FB"};
 s.addText("二手電腦詢價系統 — 商業分析",{x:0.5,y:1.6,w:9,h:1,fontSize:30,bold:true,color:"2F5496"});
 s.addText("標的："+bizTopicName,{x:0.5,y:2.7,w:9,h:0.6,fontSize:18,color:"333333"});
 s.addText("產製："+APP.date+"　|　Claude Code",{x:0.5,y:4.7,w:9,h:0.4,fontSize:11,color:"888888"});
 s=p.addSlide();s.addText("波特五力分析",{x:0.4,y:0.3,w:9,h:0.6,fontSize:22,bold:true,color:"2F5496"});
 const ffH=["力","壓力","結論","要點"].map(h=>({text:h,options:{bold:true,color:"FFFFFF",fill:"2F5496"}}));
 const ffR=(APP.fiveForces||[]).map(f=>[{text:String(f.name),options:{bold:true}},String(f.score)+"/5",String(f.summary||""),(f.points||[]).join("\n")]);
 s.addTable([ffH].concat(ffR),{x:0.3,y:1,w:9.4,fontSize:9,valign:"top",border:{type:"solid",color:"DDDDDD"},colW:[1.8,0.8,2.8,4]});
 s=p.addSlide();s.addText("商業模式圖 BMC",{x:0.4,y:0.3,w:9,h:0.6,fontSize:22,bold:true,color:"2F5496"});
 const bH=["區塊","內容"].map(h=>({text:h,options:{bold:true,color:"FFFFFF",fill:"2F5496"}}));
 const bR=(APP.bmc||[]).map(b=>[{text:String(b.title),options:{bold:true}},(b.items||[]).join("\n")]);
 s.addTable([bH].concat(bR),{x:0.3,y:1,w:9.4,fontSize:8,valign:"top",border:{type:"solid",color:"DDDDDD"},colW:[2.2,7.2]});
 s=p.addSlide();s.addText("SWOT 分析",{x:0.4,y:0.3,w:9,h:0.6,fontSize:22,bold:true,color:"2F5496"});
 const SW=APP.swot||{};const quad=(t,arr,x,y,fill)=>s.addText([{text:t+"\n",options:{bold:true,fontSize:13}}].concat((arr||[]).map(i=>({text:"• "+i+"\n",options:{fontSize:9}}))),{x:x,y:y,w:4.6,h:1.95,fill:fill,color:"222222",valign:"top",margin:6});
 quad("優勢 S",SW.strengths,0.3,1,"ECFDF5");quad("劣勢 W",SW.weaknesses,5.1,1,"FFF7ED");
 quad("機會 O",SW.opportunities,0.3,3.05,"EFF6FF");quad("威脅 T",SW.threats,5.1,3.05,"FEF2F2");
 p.writeFile({fileName:"商業分析_"+bizTopicName+".pptx"});
};

/* ---------- 語言 + 顧問報告 ---------- */
let lang="zh";try{lang=localStorage.getItem("pcf-lang")||"zh"}catch(e){}
const L=(o)=>(o&&typeof o==="object"&&!Array.isArray(o))?(o[lang]||o.zh||o.en||""):(o||"");
const TT={zh:{guide:"📖 使用指南",flows:"🔀 運作流程圖",market:"🌐 市場與文獻",critique:"🎯 誠實紅隊評估",money:"💰 變現・定價・行動計畫",refs:"參考來源",sev:"嚴重度",rebut:"回應",verdict:"總評",how:"做法",pot:"潛力/限制",models:"變現模式",plan:"行動計畫"},
 en:{guide:"📖 User Guide",flows:"🔀 How It Works",market:"🌐 Market & Literature",critique:"🎯 Honest Red-Team",money:"💰 Monetize · Pricing · Action",refs:"References",sev:"Severity",rebut:"Rebuttal",verdict:"Verdict",how:"How",pot:"Potential/Limit",models:"Models",plan:"Action Plan"}};
const tr=k=>(TT[lang]||TT.zh)[k];
const UI={zh:{
 brand:"🖥️ 二手電腦詢價系統",brandSub:"全球前10大平台比價・相容查詢・防詐客服",
 aiPanelLabel:"AI 代理網址(Cloudflare Worker）— 留空則用規則式／手動版",aiSave:"儲存",aiTest:"測試連線",
 goAll:"一鍵全開",kwPh:"輸入型號或品名，例：i7-6700、H110M-K D3、MacBook Pro",
 fAll:"全部",fTw:"🇹🇼 台灣平台",fIntl:"🌐 國際／整新",loadLine:"📂 載入 LINE 對話 txt 抓型號",bmk:"⭐ 一鍵比價書籤（拖到書籤列）",bmkTitle:"拖到書籤列",
 hPlatforms:"🏆 全球前 10 大二手電腦平台",hRules:"🛡️ 防詐下單鐵則",hTpl:"📝 詢價範本",copy:"複製",
 hSellers:"✅ 高評價賣家直達（依露天評價數實查）",sellersNote:"客觀標示、非背書：依露天評價數／好評率實查彙整，僅供參考，請自行查證。",hPrice:"📋 賣價對照表",
 hCompat:"🧩 零件相容性檢查",lCpu:"CPU 處理器",lBoard:"主機板",lRam:"記憶體類型",ramNone:"（先不選）",checkCompat:"檢查相容性",
 hCompare:"📐 規格比較表",comparePick:"勾選下方零件，產生規格比較表。",genCompare:"產生比較表",h3Cpu:"CPU 規格庫",h3Board:"主機板規格庫",h3Ram:"記憶體規格",hRules2:"📏 相容性判斷規則",
 hPhoto:"📷 拍照／上傳 找相容零件",upload:"🖼️ 上傳照片",openCam:"📸 開啟相機",shoot:"拍照",photoModelLabel:"輸入照片上看到的型號（晶片/主板絲印），自動查相容＋比價",photoModelPh:"例：i7-6700、H110M-K D3、DDR3L 8G",photoFind:"🔎 拿去比價",lens:"🔍 Google Lens 以圖搜尋",aiVision:"🤖 AI 辨識這張照片（需設定 AI)",
 photoNote:"⚠️ 誠實說明：純靜態網站<b>無法自動辨識</b>照片裡的晶片（那需要 AI 後端）。未設定 AI 時做的是「拍照／上傳留存 ＋ 你輸入型號 → 自動查相容性＋一鍵比價」；設定 AI 後可按「🤖 AI 辨識」真讀型號。",
 bizLabel:"分析標的(預設「本系統」;輸入任意公司／產品,需設定 AI 才會動態產生)",bizTopicPh:"例:二手筆電回收事業、某新創 App",bizGen:"動態產生",pptBtn:"⬇️ 下載 PPT（封面＋五力＋BMC＋SWOT）",bizTitle:"📊 波特五力分析（本系統）",hBmc:"🧱 商業模式圖 BMC",hSwot:"🎯 SWOT 分析",
 hFaq:"💬 規則式 FAQ 客服",faqNote:"問「DDR3L 能用嗎」「賣家叫我取消」「嗶兩聲沒畫面」等都行。規則式問答<b>人人可用</b>;<b>真 AI 客服僅開放審核通過的會員</b>(右上 ⚙️ 填 AI 網址+會員碼)。",askPh:"輸入你的問題…",ask:"問",hFaqList:"📚 常見問題（點開看答案）",
 tagTw:"🇹🇼 台灣",tagIntl:"🌐 國際",needKw:"先輸入關鍵字",common:"常搜：",gotoStore:"前往賣場",verdictOk:"✅ 可相容",verdictBad:"❌ 不相容",thinking:"🤖 思考中…",
 footer:"資料更新：{date}　|　只開各平台<b>真實搜尋</b>，不爬價、不造假快取價，價格以平台即時頁面為準。<br>個人比價與防詐用途，使用前自行判斷賣家信用。一律貨到付款、收到先驗、不對拒收。<br>🤖 以 Claude Code 製作",
 thCpu:["","型號","腳位","世代","核心緒","TDP","記憶體支援"],thBoard:["","型號","腳位","晶片組","記憶體","插槽","最大","板型"],thRam:["類型","電壓","插槽","說明"],thCmp:["型號","類型","腳位","世代/晶片組","核緒/板型","TDP/最大","記憶體","備註"],
 zoomLbl:"縮放",hSpec:"🧾 各廠商完整 SPEC 與比價報告",hQuote:"🧮 報價單(可匯出/匯入)",qAdd:"＋ 新增一列",qXls:"⬇️ 匯出 XLS",qPdf:"🖨 匯出 PDF(列印)",qImp:"⬆️ 匯入 XLS",
 qNote:"匯出 XLS 可在 Excel 開啟編輯,之後可再「匯入」回本頁繼續;PDF 走系統列印(選「儲存為 PDF」)。",
 qth:["項目","規格","數量","單價 NT$","小計","賣家/來源","備註",""],qTotalLbl:"總計 NT$",qTitle:"二手電腦零件報價單",
 thBoards:["廠牌","型號","腳位","晶片組","記憶體","板型","關鍵 I/O","二手行情","優點","缺點"],thCpus2:["型號","核心/緒","時脈","TDP","二手行情","CP 值評註"],thRel:["型號","關鍵規格","行情","選購提醒"],
 designH:"🎨 設計優化依據(世界前 10 大二手網站)",flowReplay:"▶ 重播動畫",refsH:"參考文獻(依編號順序)",formulaH:"評估公式",compH:"跨廠牌優缺點比較",delRow:"刪",
 aiMemberLabel:"會員碼 — AI 客服僅開放審核通過的會員(向站長申請)",aiMemberPh:"例:BRO-2026",
 memberErr:"🔒 AI 客服僅開放審核通過的會員。請向站長申請會員碼,並在右上 ⚙️ 填入。",
 memberMiss:"ℹ️ 尚未填會員碼:若站長已開啟會員審核,AI 會拒絕並自動退回規則式。",
 aiOn:"✅ 已啟用真 AI:FAQ 客服與拍照辨識會用 AI;商業分析可動態產生。",
 aiOff:"未設定:FAQ 用規則式、拍照用手動型號、商業分析用內建。設定後升級成真 AI(需會員碼)。",
 deckOpen:"🎬 播放動態簡報(SPEC 比價・雷達・自動播放)",dailyTip:"每日提示",dailyPick:"今日精選搜尋",official:"官網圖",
 photoHint:"📷 = 原廠產品頁(含官方實品照)。基於版權與連結時效,本站不內嵌原廠照片,一律連回原廠來源。",
 schemNote:"主機板示意圖(自繪,非實品照;實品照請點各列 📷 官網圖)"
},en:{
 brand:"🖥️ Second-hand PC Price Finder",brandSub:"Top-10 platforms · compatibility · anti-scam",
 aiPanelLabel:"AI proxy URL (Cloudflare Worker) — blank = rule-based/manual",aiSave:"Save",aiTest:"Test",
 goAll:"Open all",kwPh:"Enter a model or name, e.g. i7-6700, H110M-K D3, MacBook Pro",
 fAll:"All",fTw:"🇹🇼 Taiwan",fIntl:"🌐 Global/Refurb",loadLine:"📂 Load LINE .txt → extract models",bmk:"⭐ Compare bookmarklet (drag to bar)",bmkTitle:"Drag to bookmarks bar",
 hPlatforms:"🏆 Top 10 second-hand PC platforms",hRules:"🛡️ Anti-scam ordering rules",hTpl:"📝 Inquiry template",copy:"Copy",
 hSellers:"✅ High-rated sellers (by verified Ruten review counts)",sellersNote:"Objective labels, not endorsements: compiled from Ruten review counts/positive rates for reference only — verify yourself.",hPrice:"📋 Price tables",
 hCompat:"🧩 Part compatibility check",lCpu:"CPU",lBoard:"Motherboard",lRam:"Memory type",ramNone:"(none)",checkCompat:"Check",
 hCompare:"📐 Spec comparison",comparePick:"Tick parts below to build a comparison table.",genCompare:"Build table",h3Cpu:"CPU library",h3Board:"Motherboard library",h3Ram:"Memory specs",hRules2:"📏 Compatibility rules",
 hPhoto:"📷 Photo/upload to find parts",upload:"🖼️ Upload",openCam:"📸 Camera",shoot:"Capture",photoModelLabel:"Type the model you see (chip/board silkscreen) → auto compatibility + compare",photoModelPh:"e.g. i7-6700, H110M-K D3, DDR3L 8G",photoFind:"🔎 Compare it",lens:"🔍 Google Lens",aiVision:"🤖 AI-identify this photo (needs AI)",
 photoNote:"⚠️ Honest note: a static site <b>can't auto-identify</b> the chip (that needs an AI backend). Without AI it keeps the photo + you type the model → auto compatibility + one-click compare; with AI set, hit “🤖 AI-identify” to read the model for you.",
 bizLabel:"Analysis subject (default: this system; any company/product — needs AI to generate)",bizTopicPh:"e.g. used-laptop recycling, a startup app",bizGen:"Generate",pptBtn:"⬇️ Download PPT (cover + 5 Forces + BMC + SWOT)",bizTitle:"📊 Porter's Five Forces (this system)",hBmc:"🧱 Business Model Canvas",hSwot:"🎯 SWOT",
 hFaq:"💬 FAQ assistant",faqNote:"Ask things like “can I use DDR3L”, “seller asked me to cancel”, “two beeps no display”. The rule-based FAQ is <b>open to everyone</b>; the <b>real AI assistant is for approved members only</b> (set the AI URL + member code in ⚙️).",askPh:"Ask a question…",ask:"Ask",hFaqList:"📚 FAQ (tap to expand)",
 tagTw:"🇹🇼 TW",tagIntl:"🌐 Intl",needKw:"Enter a keyword first",common:"Common:",gotoStore:"Visit store",verdictOk:"✅ Compatible",verdictBad:"❌ Not compatible",thinking:"🤖 Thinking…",
 footer:"Updated {date}　|　Opens each platform's <b>real search</b> — no scraping, no fake cached prices; prices are live on each platform.<br>For personal comparison & anti-scam use; judge seller credibility yourself. Always cash-on-delivery, inspect on arrival, refuse if wrong.<br>🤖 Built with Claude Code",
 thCpu:["","Model","Socket","Gen","Cores/Threads","TDP","Memory"],thBoard:["","Model","Socket","Chipset","Memory","Slots","Max","Form"],thRam:["Type","Voltage","Slot","Note"],thCmp:["Model","Type","Socket","Gen/Chipset","Cores/Form","TDP/Max","Memory","Note"],
 zoomLbl:"Zoom",hSpec:"🧾 Full vendor SPEC & price-comparison report",hQuote:"🧮 Quotation (export/import)",qAdd:"＋ Add row",qXls:"⬇️ Export XLS",qPdf:"🖨 Export PDF (print)",qImp:"⬆️ Import XLS",
 qNote:"The exported XLS opens in Excel for editing and can be re-imported here; PDF uses the system print dialog (choose “Save as PDF”).",
 qth:["Item","Spec","Qty","Unit NT$","Subtotal","Seller/Source","Note",""],qTotalLbl:"Total NT$",qTitle:"Second-hand PC Parts Quotation",
 thBoards:["Brand","Model","Socket","Chipset","Memory","Form","Key I/O","Used price","Pros","Cons"],thCpus2:["Model","Cores/Threads","Clock","TDP","Used price","Value note"],thRel:["Model","Key spec","Price","Buying note"],
 designH:"🎨 Design rationale (world's top-10 second-hand sites)",flowReplay:"▶ Replay animation",refsH:"References (numbered)",formulaH:"Evaluation formula",compH:"Cross-vendor pros & cons",delRow:"Del",
 aiMemberLabel:"Member code — the AI assistant is for approved members only (ask the site owner)",aiMemberPh:"e.g. BRO-2026",
 memberErr:"🔒 The AI assistant is for approved members only. Ask the site owner for a member code and enter it in ⚙️ (top-right).",
 memberMiss:"ℹ️ No member code yet: if the owner enabled member review, AI requests will be rejected and fall back to the rule-based FAQ.",
 aiOn:"✅ Real AI enabled: the FAQ assistant and photo recognition use AI; business analysis can be generated dynamically.",
 aiOff:"Not set: FAQ uses rules, photo uses manual model entry, business analysis uses built-in data. Configure to upgrade to real AI (member code required).",
 deckOpen:"🎬 Play dynamic deck (SPEC comparison · radar · autoplay)",dailyTip:"Tip of the day",dailyPick:"Today's pick",official:"Official",
 photoHint:"📷 = official product page (with the vendor's real photos). For copyright and link-freshness reasons this site links to the source instead of embedding vendor photos.",
 schemNote:"Schematic motherboard illustration (drawn, not a real photo; tap 📷 per row for official photos)"
}};
const ui=k=>{const v=(UI[lang]||UI.zh)[k];return v!=null?v:k;};
function applyUI(){
 $$("[data-i18n]").forEach(e=>{const v=ui(e.dataset.i18n);if(v!=null)e.textContent=v;});
 $$("[data-i18n-ph]").forEach(e=>{const v=ui(e.dataset.i18nPh);if(v!=null)e.placeholder=v;});
 $$("[data-i18n-html]").forEach(e=>{const v=ui(e.dataset.i18nHtml);if(v!=null)e.innerHTML=v;});
 $$("[data-i18n-title]").forEach(e=>{const v=ui(e.dataset.i18nTitle);if(v!=null)e.title=v;});
}
function applyLang(){document.documentElement.lang=lang==="zh"?"zh-Hant":"en";$("#langBtn").textContent=lang==="zh"?"EN":"中";
 $$("#nav button").forEach(b=>{const v=lang==="zh"?b.dataset.zh:b.dataset.en;if(v)b.textContent=v;});
 applyUI();renderStatic();renderPlatforms();renderSellers();renderCompat();renderConsult();renderSpec();renderDaily();}
$("#langBtn").onclick=()=>{lang=lang==="zh"?"en":"zh";try{localStorage.setItem("pcf-lang",lang)}catch(e){}applyLang();};

function flowSVG(flow){const N=flow.nodes||[],E=flow.edges||[],idx={};N.forEach((n,i)=>idx[n.id]=i);
 const ROW=92,CX=170,W=270,H=46,top=18;
 const cut=s=>{s=String(s);return s.length>24?s.slice(0,23)+"…":s;};
 const txt=(s,x,y)=>'<text x="'+x+'" y="'+(y+4)+'" font-size="12" text-anchor="middle" fill="#1f2430">'+esc(cut(s))+'</text>';
 const shape=(n,y)=>{const x=CX-W/2;
  if(n.type==="decision"){const cy=y+H/2,dx=W/2,dy=H/1.3;return '<polygon points="'+CX+','+(cy-dy)+' '+(CX+dx)+','+cy+' '+CX+','+(cy+dy)+' '+(CX-dx)+','+cy+'" fill="#fff7ed" stroke="#e8c84d" stroke-width="2"/>'+txt(L(n.label),CX,cy);}
  const round=(n.type==="start"||n.type==="end")?H/2:12,fill=n.type==="start"?"#dcfce7":n.type==="end"?"#e0e7ff":"#eef2fb";
  return '<rect x="'+x+'" y="'+y+'" width="'+W+'" height="'+H+'" rx="'+round+'" fill="'+fill+'" stroke="#9bb0d6"/>'+txt(L(n.label),CX,y+H/2);};
 let g='';
 E.forEach(e=>{const si=idx[e.from],ti=idx[e.to];if(si==null||ti==null)return;const lab=L(e.label);const dl=' class="fedge" style="animation-delay:'+(0.25+si*0.28)+'s"';
  if(ti===si+1){const y1=top+si*ROW+H,y2=top+ti*ROW;g+='<line'+dl+' x1="'+CX+'" y1="'+y1+'" x2="'+CX+'" y2="'+(y2-2)+'" stroke="#7c8aa6" stroke-width="1.6" marker-end="url(#ar)"/>';if(lab)g+='<text x="'+(CX+7)+'" y="'+((y1+y2)/2)+'" font-size="11" fill="#b45309">'+esc(lab)+'</text>';}
  else{const sy=top+si*ROW+H/2,ey=top+ti*ROW+H/2,gx=CX+W/2+46;g+='<path'+dl+' d="M'+(CX+W/2)+','+sy+' H'+gx+' V'+ey+' H'+(CX+W/2)+'" fill="none" stroke="#7c8aa6" stroke-width="1.6" marker-end="url(#ar)"/>';if(lab)g+='<text x="'+(gx+3)+'" y="'+((sy+ey)/2)+'" font-size="11" fill="#b45309">'+esc(lab)+'</text>';}});
 N.forEach((n,i)=>g+='<g class="fnode" style="animation-delay:'+(i*0.28)+'s">'+shape(n,top+i*ROW)+'</g>');
 const ht=top+N.length*ROW;
 return '<svg viewBox="0 0 '+(CX+W/2+80)+' '+ht+'" width="100%" style="max-width:420px"><defs><marker id="ar" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 z" fill="#7c8aa6"/></marker></defs>'+g+'</svg>';}

function barChart(bars){bars=bars||[];const max=Math.max(...bars.map(b=>b.value||0),1),bh=30,gap=16,top=8,h=top+bars.length*(bh+gap);let g='';
 bars.forEach((b,i)=>{const y=top+i*(bh+gap),w=Math.max(2,(b.value/max)*250);
  g+='<text x="0" y="'+(y+bh/2+4)+'" font-size="11.5" fill="var(--ink)">'+esc(L(b.label))+'</text>';
  g+='<rect class="fbar" style="animation-delay:'+(i*0.15)+'s" x="250" y="'+y+'" width="'+w+'" height="'+bh+'" rx="5" fill="var(--accent2)"/>';
  g+='<text x="'+(254+w)+'" y="'+(y+bh/2+4)+'" font-size="12" font-weight="700" fill="var(--ink)">'+esc(String(b.value))+'</text>';});
 return '<svg viewBox="0 0 560 '+h+'" width="100%" style="margin:8px 0">'+g+'</svg>';}

function refItem(r,n){return '<div class="ref"><div><a class="refnum" '+(r.url?'href="'+r.url+'" target="_blank" rel="noopener"':'')+'>['+n+']</a> '+esc(r.title)+' <span class="muted">— '+esc(r.source)+'</span></div>'+(r.takeaway?'<div class="big2">'+esc(L(r.takeaway))+'</div>':'')+'</div>';}
function animate(sel){$$(sel).forEach(el=>{el.classList.remove("anim");void el.offsetWidth;el.classList.add("anim");});}
function renderConsult(){const C=APP.consult||{};const R=APP.research||{};if(!C.guide){$("#cIntro").innerHTML='<div class="note">尚無顧問報告資料。</div>';return;}
 const P=R.polish||{};
 $("#cIntro").innerHTML=P.intro?esc(L(P.intro)):(lang==="zh"
  ?"本報告參考<b>國際期刊、產業報告與企業公開資訊</b>(文獻依編號列於各節末),以顧問角度<b>誠實</b>評估本系統。右上 <b>EN</b> 可切換英文。"
  :"This consultant report draws on <b>international journals, industry reports and public company information</b> (numbered references per section) for an <b>honest</b> assessment. Use <b>中</b> (top-right) for Chinese.");
 $("#cH_guide").textContent=tr("guide");$("#cH_flows").textContent=tr("flows");$("#cH_market").textContent=tr("market");$("#cH_critique").textContent=tr("critique");$("#cH_money").textContent=tr("money");
 const g=C.guide;
 const qs=(P.quickstart&&P.quickstart.length?P.quickstart:g.quickstart)||[];
 const eli=P.eli20||g.eli15;const eliTag=P.eli20?"ELI20":"ELI15";
 $("#cGuide").innerHTML='<div class="card"><ol class="big">'+qs.map(s=>"<li>"+esc(L(s))+"</li>").join("")+'</ol></div>'+
  '<div class="card eli"><b>'+eliTag+'</b><div class="big" style="margin-top:5px">'+esc(L(eli))+'</div></div>'+
  (g.examples||[]).map(e=>'<div class="card"><b>'+esc(L(e.scenario))+'</b><div class="big2" style="margin-top:5px">'+esc(L(e.walkthrough)).replace(/\n/g,"<br>")+'</div></div>').join("");
 $("#cFlows").innerHTML=((C.flows&&C.flows.flows)||[]).map((f,i)=>'<div class="card"><h3>'+esc(L(f.title))+'</h3><div class="flowwrap"><div class="flowimg anim" data-flow="'+i+'">'+flowSVG(f)+'</div><div class="flowdesc big2">'+esc(L(f.desc)).replace(/\n/g,"<br>")+'<br><button class="replay" data-rp=".flowimg[data-flow=\''+i+'\']">'+ui("flowReplay")+'</button></div></div></div>').join("");
 const m=C.market;
 const mrefs=m.references||[],drefs=(R.design&&R.design.references)||[];
 let refN=0;
 $("#cMarket").innerHTML='<div class="card"><ul class="big">'+(m.market_points||[]).map(p=>"<li>"+esc(L(p))+"</li>").join("")+'</ul></div>'+
  '<div class="card anim" id="mChart"><b>'+esc(L(m.chart.title))+'</b>'+barChart(m.chart.bars)+'<div class="note">'+esc(L(m.chart.caption))+'</div><button class="replay" data-rp="#mChart">'+ui("flowReplay")+'</button></div>'+
  (R.design?('<div class="card"><b>'+ui("designH")+'</b><div class="big2" style="margin:6px 0">'+esc(L(R.design.eyecare))+'</div>'+
   '<div class="reflist">'+(R.design.sites||[]).map(s=>'<div class="ref"><b>'+esc(s.name)+'</b> <span class="muted">'+esc(s.url)+'</span><div class="big2">'+esc(L(s.pattern))+'</div></div>').join("")+'</div>'+
   '<ul class="big2">'+(R.design.takeaways||[]).map(t=>'<li><b>'+esc(L(t.principle))+'</b>：'+esc(L(t.applied))+'</li>').join("")+'</ul></div>'):"")+
  '<div class="card"><b>'+ui("refsH")+'</b><div class="reflist">'+mrefs.map(r=>refItem(r,++refN)).join("")+drefs.map(r=>refItem(r,++refN)).join("")+'</div></div>';
 $$("#cFlows .replay, #cMarket .replay").forEach(b=>b.onclick=()=>animate(b.dataset.rp));
 const cr=C.critique;
 $("#cCritique").innerHTML='<div class="card"><div class="verdict bad" style="font-size:1.04rem"><b>⚖ '+tr("verdict")+'：</b>'+esc(L(cr.verdict))+'</div></div>'+
  '<details class="card"><summary style="cursor:pointer;font-weight:700">'+(lang==="zh"?"▸ 展開完整紅隊評估（內含對本案的嚴厲批評；點此展開）":"▸ Expand full red-team critique (harsh by design — tap to open)")+'</summary>'+
  '<div style="margin-top:10px"><b>Truth</b><ul class="big2">'+(cr.truth||[]).map(x=>"<li>"+esc(L(x))+"</li>").join("")+'</ul></div>'+
  '<div><b>Red-Team</b>'+(cr.redteam||[]).map(x=>'<div class="rt"><span class="sev s'+(x.severity||3)+'">'+tr("sev")+' '+(x.severity||3)+'</span><span class="big2">'+esc(L(x.attack))+'</span><div class="muted" style="margin-top:3px">'+tr("rebut")+'：'+esc(L(x.rebuttal))+'</div></div>').join("")+'</div>'+
  '<div><b>Blind Spots</b><ul class="big2">'+(cr.blindspots||[]).map(x=>"<li>"+esc(L(x))+"</li>").join("")+'</ul></div>'+
  '</details>';
 const mo=C.monetize;
 $("#cMoney").innerHTML='<div class="card"><b>'+tr("models")+'</b>'+(mo.models||[]).map(x=>'<div class="rt"><b>'+esc(L(x.name))+'</b><div class="big2">'+tr("how")+'：'+esc(L(x.how))+'</div><div class="muted">'+tr("pot")+'：'+esc(L(x.potential))+'</div></div>').join("")+'</div>'+
  '<div class="pricegrid">'+(mo.pricing||[]).map(x=>'<div class="pcard2"><div class="ptier">'+esc(L(x.tier))+'</div><div class="pprice">'+esc(L(x.price))+'</div><div class="big2">'+esc(L(x.features)).replace(/\n/g,"<br>")+'</div></div>').join("")+'</div>'+
  '<div class="card"><b>'+tr("plan")+'</b>'+(mo.action_plan||[]).map(x=>'<div class="rt"><b>'+esc(L(x.phase))+' <span class="muted">'+esc(L(x.timeframe))+'</span></b><div class="big2" style="margin-top:3px">'+esc(L(x.steps)).replace(/\n/g,"<br>")+'</div><div class="muted">KPI：'+esc(L(x.kpi))+'</div></div>').join("")+'</div>';
}

renderStatic();renderPlatforms();renderSellers();renderCompat();renderBiz();renderFaqList();refreshAIStatus();applyLang();
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
