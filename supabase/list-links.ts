// Edge Function "list-links" (verify_jwt = false)
// Déployée sur le projet Supabase hpowqowzrxqokikadwni.
import "jsr:@supabase/functions-js/edge-runtime.d.ts";

const SUPABASE_URL = Deno.env.get("SUPABASE_URL")!;
const SERVICE_ROLE = Deno.env.get("SUPABASE_SERVICE_ROLE_KEY")!;

const cors = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Headers": "authorization, x-client-info, apikey, content-type",
  "Access-Control-Allow-Methods": "GET, OPTIONS",
};

function json(obj: unknown, status = 200) {
  return new Response(JSON.stringify(obj), {
    status,
    headers: { ...cors, "Content-Type": "application/json" },
  });
}

Deno.serve(async (req: Request) => {
  if (req.method === "OPTIONS") return new Response("ok", { headers: cors });
  try {
    const url = new URL(req.url);
    const brand = url.searchParams.get("brand");
    const q = url.searchParams.get("q");
    let limit = parseInt(url.searchParams.get("limit") || "200", 10);
    if (isNaN(limit) || limit < 1 || limit > 1000) limit = 200;

    let path = `tracked_links?select=*&order=created_at.desc&limit=${limit}`;
    if (brand) path += `&brand=eq.${encodeURIComponent(brand)}`;
    if (q) {
      const s = q.replace(/[()*,]/g, " ").trim();
      if (s) {
        const like = `*${s}*`;
        path += `&or=(utm_campaign.ilike.${encodeURIComponent(like)},final_url.ilike.${encodeURIComponent(like)},created_by.ilike.${encodeURIComponent(like)},utm_source.ilike.${encodeURIComponent(like)})`;
      }
    }

    const r = await fetch(`${SUPABASE_URL}/rest/v1/${path}`, {
      headers: { apikey: SERVICE_ROLE, Authorization: `Bearer ${SERVICE_ROLE}` },
    });
    if (!r.ok) {
      const err = await r.text();
      return json({ error: "query failed", detail: err }, 500);
    }
    const rows = await r.json();
    return json(rows);
  } catch (e) {
    return json({ error: String(e) }, 500);
  }
});
