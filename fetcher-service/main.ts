// cec/deno_api/main.ts
import { serve } from "https://deno.land/std@0.140.0/http/server.ts";
import { logger } from "./logger.ts";

logger.info("Deno HTML fetcher API starting");

serve(async (req) => {
  const url = new URL(req.url);
  if (url.pathname === "/fetch") {
    const targetUrl = url.searchParams.get("url");
    const userAgent = Deno.env.get("USER_AGENT"); // Read from environment variable
    if (!targetUrl) {
      return new Response("Missing 'url' query parameter", { status: 400 });
    }
    try {
      logger.info(`Fetching ${targetUrl}`);
      const headers = new Headers();
      if (userAgent) {
        headers.set("User-Agent", userAgent);
      }
      const resp = await fetch(targetUrl, { headers: headers });
      // Ensure the response is ok before proceeding
      if (!resp.ok) {
        throw new Error(`Failed to fetch: ${resp.status} ${resp.statusText}`);
      }
      const source = await resp.text();
      return new Response(source, { headers: { "Content-Type": "text/html" } });
    } catch (e) {
        logger.error(`Error fetching URL: ${targetUrl}`, e);
        const message = e instanceof Error ? e.message : "Unexpected fetch error";
        return new Response(message, { status: 500 });
    }
  } else if (url.pathname === "/health") {
    return new Response("OK", { status: 200 });
  }
  return new Response("Not Found", { status: 404 });
}, { port: 8000 });

logger.info("Deno HTML fetcher API running on http://localhost:8000");
