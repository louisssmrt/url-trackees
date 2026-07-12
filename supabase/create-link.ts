// Edge Function "create-link" (verify_jwt = false)
// Déployée sur le projet Supabase hpowqowzrxqokikadwni.
// Aucun secret ici : le token Bitly est lu dans la table app_config via la service_role.
import "jsr:@supabase/functions-js/edge-runtime.d.ts";

const SUPABASE_URL = Deno.env.get("SUPABASE_URL")!;
const SERVICE_ROLE = Deno.env.get("SUPABASE_SERVICE_ROLE_KEY")!;

const cors = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Headers": "authorization, x-client-info, apikey, content-type",
  "Access-Control-Allow-Methods": "POST, OPTIONS",
};

function json(obj: unknown, status = 200) {
  return new Response(JSON.stringify(obj), {
    status,
    headers: { ...cors, "Content-Type": "application/json" },
  });
}

function sbFetch(path: string, init: RequestInit = {}) {
  const headers = {
    apikey: SERVICE_ROLE,
    Authorization: `Bearer ${SERVICE_ROLE}`,
    "Content-Type": "application/json",
    ...(init.headers || {}),
  };
  return fetch(`${SUPABASE_URL}/rest/v1/${path}`, { ...init, headers });
}

Deno.serve(async (req: Request) => {
  if (req.method === "OPTIONS") return new Response("ok", { headers: cors });
  if (req.method !== "POST") return json({ error: "method not allowed" }, 405);

  try {
    const b = await req.json();
    const required = ["brand", "base_url", "utm_source", "utm_medium", "utm_campaign", "final_url"];
    for (const k of required) {
      if (!b[k] || String(b[k]).trim() === "") return json({ error: `champ manquant: ${k}` }, 400);
    }

    let short_url: string | null = null;
    if (b.want_short) {
      const r = await sbFetch("app_config?key=eq.bitly_token&select=value");
      const rows = await r.json();
      const token = rows?.[0]?.value;
      if (token) {
        const resp = await fetch("https://api-ssl.bitly.com/v4/shorten", {
          method: "POST",
          headers: { Authorization: `Bearer ${token}`, "Content-Type": "application/json" },
          body: JSON.stringify({ long_url: b.final_url }),
        });
        if (resp.ok) {
          const data = await resp.json();
          short_url = data.link || null;
        }
      }
    }

    const row = {
      created_by: b.created_by || null,
      brand: b.brand,
      base_url: b.base_url,
      utm_source: b.utm_source,
      utm_medium: b.utm_medium,
      utm_campaign: b.utm_campaign,
      utm_term: b.utm_term || null,
      utm_content: b.utm_content || null,
      final_url: b.final_url,
      short_url,
      notes: b.notes || null,
    };

    const ins = await sbFetch("tracked_links", {
      method: "POST",
      headers: { Prefer: "return=representation" },
      body: JSON.stringify(row),
    });
    if (!ins.ok) {
      const err = await ins.text();
      return json({ error: "insert failed", detail: err }, 500);
    }
    const inserted = await ins.json();
    return json({ ok: true, id: inserted?.[0]?.id ?? null, short_url });
  } catch (e) {
    return json({ error: String(e) }, 500);
  }
});
