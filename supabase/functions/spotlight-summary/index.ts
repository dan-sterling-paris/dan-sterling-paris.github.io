// spotlight-summary — fetches a Spotlight profile via their public API and returns a summary
// GET /functions/v1/spotlight-summary?url=<encoded_spotlight_url>

import { json, cors } from "../_shared/supabase.ts";

function extractPin(url: string): string | null {
  const match = url.match(/(\d{4}-\d{4}-\d{4})/);
  return match ? match[1] : null;
}

Deno.serve(async (req: Request) => {
  if (req.method === "OPTIONS") return cors();
  if (req.method !== "GET") return json({ error: "Method not allowed" }, 405);

  const url = new URL(req.url).searchParams.get("url");
  if (!url) return json({ error: "Missing url parameter" }, 400);

  const pin = extractPin(url);
  if (!pin) return json({ error: "Could not extract Spotlight PIN from URL" }, 400);

  try {
    const response = await fetch(`https://profileapi.spotlight.com/profiles/view/${pin}`, {
      headers: {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
      },
    });

    if (!response.ok) {
      return json({ error: `Spotlight API returned ${response.status}` }, 502);
    }

    const data = await response.json();

    const headshot = data.mainPhoto?.url || "";

    const agencies = (data.agents || []).map((a: Record<string, unknown>) => a.name || "").filter(Boolean);

    const training = data.training?.notes || "";

    const allCredits = (data.credits?.credits || []) as Array<Record<string, unknown>>;
    const topCredits = allCredits.slice(0, 5).map((c) => ({
      title: c.name || "",
      role: c.role || "",
      year: c.dateTo ? new Date(c.dateTo as string).getFullYear().toString() : "",
      company: c.company || "",
    }));

    return json({
      headshot,
      agencies,
      training,
      credits: topCredits,
    });
  } catch (err) {
    return json({ error: `Fetch error: ${(err as Error).message}` }, 500);
  }
});
