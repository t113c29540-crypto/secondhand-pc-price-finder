/**
 * 二手電腦詢價系統 — AI 代理 (Cloudflare Worker)
 * ================================================
 * 金鑰只存在 Worker 的密鑰環境變數,前端只呼叫這個代理,金鑰永不外露。
 *
 * 支援三種模式 (POST JSON: { mode, ... }):
 *   - chat     : { messages:[{role,content}], }          → 規則式FAQ升級成真 AI 客服(繁中、防詐、相容性)
 *   - vision   : { image:"<base64>", media_type:"image/jpeg" } → 辨識照片中的電腦零件,回 JSON
 *   - analysis : { topic:"<主題>" }                       → 產生五力/BMC/SWOT JSON(供動態商業分析+PPT)
 *
 * 環境變數 (wrangler secret / vars):
 *   PROVIDER         : "anthropic"(預設) | "openai"
 *   MODEL            : 預設 claude-opus-4-8;省錢可設 claude-haiku-4-5 / claude-sonnet-4-6 / gpt-4o-mini
 *   ANTHROPIC_API_KEY: PROVIDER=anthropic 時必填(密鑰)
 *   OPENAI_API_KEY   : PROVIDER=openai 時必填(密鑰)
 *   ALLOWED_ORIGIN   : CORS 允許來源,預設 "*";建議設成你的 Pages 網址
 *   MEMBER_CODES     : 會員審核名單(逗號分隔,例 "BRO-2026,MOM-01")。設定後所有 AI 模式
 *                      僅限持有效會員碼者;留空 = 不啟用審核。核發/撤銷 = 增刪名單後 Deploy。
 */

const SYSTEM_CHAT = `你是「二手電腦詢價系統」的繁體中文防詐客服,協助台灣使用者(常是替長輩採購)買二手電腦零件。請用繁體中文、條列、務實可執行地回答。核心知識:
- 相容性:D3 主機板吃 DDR3/DDR3L(含 1.35V),不吃 DDR4;同型號常分 D3(DDR3)與 D4(DDR4)版要認清;DDR3 與 DDR4 插槽防呆不同、物理插不上。華碩 H110M-K D3 支援 DDR3/DDR3L,可搭 i7-6700(LGA1151、第六代)。LGA1151 100/200 系列(H110/B250)支援6/7代;300系列(B360/B365)支援8/9代,兩者不互換。LGA1150(4代,如 i7-4790/i5-4590)與 LGA1151 完全不通。型號尾碼 F(如 i5-9400F)無內顯,要另配獨顯。
- 防詐交易:一律貨到付款、收到先驗(開機點亮、CPU-Z 認型號),不對就拒收;賣家標錯價想反悔要讓「賣家」自己取消(賣家因素),別自己按;貨到付款沒付錢前零風險,賣家不出貨會被記未出貨、責任在他;簡體文案(主板/內存/臺式)+淘寶圖+引導加LINE=中國跨境貨;挑賣家看評價數多、好評99%+、開店久。
- 故障:開機嗶兩聲、無畫面多為記憶體沒插好,重插記憶體與CPU、清CMOS、單條測試、確認24+8pin供電、查嗶聲代碼,未必是板子壞。
- 立場:不販售商品、不保證價格;誠實、不造假。若問題超出範圍,誠實說不確定並建議怎麼查。`;

const SYSTEM_VISION = `你是電腦硬體辨識專家。看使用者上傳的零件照片(主機板/CPU/記憶體/硬碟/顯卡/電源),盡量讀出絲印型號並判斷規格。只輸出一個 JSON 物件(不要markdown、不要多餘文字),欄位:
{"category":"主機板|CPU|記憶體|硬碟|顯卡|電源|其他","brand":"","model":"","socket":"如LGA1151/AM4(若適用)","memory_type":"DDR3/DDR3L/DDR4(若適用)","key_specs":"一句重點規格","compatibility_note":"相容性提醒(繁中),例:此為D3板配DDR3/DDR3L","confidence":"high|medium|low","caveat":"看不清楚或不確定就說明"}
所有文字用繁體中文。看不清楚就把 confidence 設 low 並在 caveat 說明。`;

const SYSTEM_ANALYSIS = `你是商業策略分析師。針對使用者給的標的,用繁體中文產出波特五力、商業模式圖(BMC)、SWOT。只輸出一個 JSON 物件(不要markdown),結構:
{"topic":"標的","fiveForces":[{"name":"既有競爭者","score":1到5整數,"summary":"一句","points":["要點","..."]}, ...五力齊全...],"bmc":[{"key":"keyPartners|keyActivities|keyResources|valueProps|customerRelationships|channels|customerSegments|costStructure|revenueStreams","title":"中文標題","items":["..."]}, ...九塊齊全...],"swot":{"strengths":["..."],"weaknesses":["..."],"opportunities":["..."],"threats":["..."]}}
每項2到4點,務實。`;

function cors(origin) {
  return {
    "Access-Control-Allow-Origin": origin || "*",
    "Access-Control-Allow-Methods": "POST, OPTIONS",
    "Access-Control-Allow-Headers": "content-type",
    "Access-Control-Max-Age": "86400",
  };
}

function json(data, status, origin) {
  return new Response(JSON.stringify(data), {
    status: status || 200,
    headers: { "content-type": "application/json; charset=utf-8", ...cors(origin) },
  });
}

// 從模型回覆字串中抽出 JSON(容忍 ```json 圍欄)
function parseLooseJSON(text) {
  if (!text) return null;
  let t = text.trim().replace(/^```(?:json)?/i, "").replace(/```$/, "").trim();
  const s = t.indexOf("{"), e = t.lastIndexOf("}");
  if (s >= 0 && e > s) t = t.slice(s, e + 1);
  try { return JSON.parse(t); } catch (_) { return null; }
}

async function callAnthropic(env, { system, messages, image, media_type, max_tokens }) {
  const model = env.MODEL || "claude-opus-4-8";
  let msgs;
  if (image) {
    msgs = [{ role: "user", content: [
      { type: "image", source: { type: "base64", media_type: media_type || "image/jpeg", data: image } },
      { type: "text", text: "請辨識這個電腦零件。" },
    ] }];
  } else {
    msgs = messages;
  }
  const r = await fetch("https://api.anthropic.com/v1/messages", {
    method: "POST",
    headers: {
      "content-type": "application/json",
      "x-api-key": env.ANTHROPIC_API_KEY,
      "anthropic-version": "2023-06-01",
    },
    body: JSON.stringify({ model, max_tokens: max_tokens || 1024, system, messages: msgs }),
  });
  const data = await r.json();
  if (!r.ok) throw new Error(data?.error?.message || ("Anthropic " + r.status));
  const block = (data.content || []).find((b) => b.type === "text");
  return block ? block.text : "";
}

async function callOpenAI(env, { system, messages, image, media_type, max_tokens }) {
  const model = env.MODEL || "gpt-4o-mini";
  let msgs;
  if (image) {
    const dataUrl = "data:" + (media_type || "image/jpeg") + ";base64," + image;
    msgs = [
      { role: "system", content: system },
      { role: "user", content: [
        { type: "text", text: "請辨識這個電腦零件。" },
        { type: "image_url", image_url: { url: dataUrl } },
      ] },
    ];
  } else {
    msgs = [{ role: "system", content: system }, ...messages];
  }
  const r = await fetch("https://api.openai.com/v1/chat/completions", {
    method: "POST",
    headers: { "content-type": "application/json", authorization: "Bearer " + env.OPENAI_API_KEY },
    body: JSON.stringify({ model, max_tokens: max_tokens || 1024, messages: msgs }),
  });
  const data = await r.json();
  if (!r.ok) throw new Error(data?.error?.message || ("OpenAI " + r.status));
  return data.choices?.[0]?.message?.content || "";
}

export default {
  async fetch(request, env) {
    const origin = env.ALLOWED_ORIGIN || "*";
    if (request.method === "OPTIONS") return new Response(null, { headers: cors(origin) });
    if (request.method !== "POST") return json({ error: "POST only" }, 405, origin);

    let body;
    try { body = await request.json(); } catch (_) { return json({ error: "invalid JSON" }, 400, origin); }

    // 會員審核:設定 MEMBER_CODES(逗號分隔)後,所有 AI 模式僅限有效會員碼
    const codes = (env.MEMBER_CODES || "").split(",").map((s) => s.trim()).filter(Boolean);
    if (codes.length) {
      const mc = String(body.member_code || "").trim();
      if (!mc || !codes.includes(mc)) {
        return json({ error: "member_required" }, 401, origin);
      }
    }

    const provider = (env.PROVIDER || "anthropic").toLowerCase();
    const call = provider === "openai" ? callOpenAI : callAnthropic;

    try {
      if (body.mode === "chat") {
        const messages = (body.messages || []).slice(-12).filter((m) => m && m.content);
        if (!messages.length) return json({ error: "no messages" }, 400, origin);
        const text = await call(env, { system: SYSTEM_CHAT, messages, max_tokens: 1024 });
        return json({ reply: text }, 200, origin);
      }
      if (body.mode === "vision") {
        if (!body.image) return json({ error: "no image" }, 400, origin);
        const text = await call(env, { system: SYSTEM_VISION, image: body.image, media_type: body.media_type, max_tokens: 1024 });
        return json({ result: parseLooseJSON(text), raw: text }, 200, origin);
      }
      if (body.mode === "analysis") {
        const topic = (body.topic || "").trim();
        if (!topic) return json({ error: "no topic" }, 400, origin);
        const text = await call(env, {
          system: SYSTEM_ANALYSIS,
          messages: [{ role: "user", content: "標的:" + topic + "\n請產出五力、BMC、SWOT 的 JSON。" }],
          max_tokens: 4096,
        });
        return json({ analysis: parseLooseJSON(text), raw: text }, 200, origin);
      }
      return json({ error: "unknown mode" }, 400, origin);
    } catch (e) {
      return json({ error: String(e.message || e) }, 502, origin);
    }
  },
};
