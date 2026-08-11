// cec/deno_api/main.ts
import { serve } from "https://deno.land/std@0.140.0/http/server.ts";
import { logger } from "./logger.ts";

const ALLOWED_FETCH_HOSTS = (Deno.env.get("ALLOWED_FETCH_HOSTS") ?? "farside.co.uk")
  .split(",")
  .map((host) => host.trim().toLowerCase())
  .filter((host) => host.length > 0);
const MAX_FETCH_SIZE_BYTES = Number(Deno.env.get("MAX_FETCH_SIZE_BYTES") ?? 1024 * 1024);
const MAX_REDIRECTS = 5;

class TargetValidationError extends Error {}

function isAllowedHost(host: string): boolean {
  const normalized = host.toLowerCase();
  return ALLOWED_FETCH_HOSTS.some((allowed) =>
    normalized === allowed || normalized.endsWith("." + allowed)
  );
}

function isPrivateIp(ip: string): boolean {
  const v4 = ip.match(/^(\d{1,3})\.(\d{1,3})\.(\d{1,3})\.(\d{1,3})$/);
  if (v4) {
    const [a, b] = [Number(v4[1]), Number(v4[2])];
    return (
      a === 0 ||
      a === 10 ||
      a === 127 ||
      (a === 100 && b >= 64 && b <= 127) || // CGNAT
      (a === 169 && b === 254) || // link-local (incl. 169.254.169.254 metadata)
      (a === 172 && b >= 16 && b <= 31) ||
      (a === 192 && b === 168) ||
      a >= 224 // multicast/reserved
    );
  }
  const lower = ip.toLowerCase();
  if (lower.includes(":")) {
    return (
      lower === "::" ||
      lower === "::1" ||
      lower.startsWith("fc") ||
      lower.startsWith("fd") || // unique local
      lower.startsWith("fe80") || // link-local
      (lower.startsWith("::ffff:") && isPrivateIp(lower.slice(7)))
    );
  }
  return false;
}

async function resolveHostIps(hostname: string): Promise<string[]> {
  const results: string[] = [];
  for (const type of ["A", "AAAA"] as const) {
    try {
      const records = await Deno.resolveDns(hostname, type);
      results.push(...records);
    } catch {
      // A host may only have one record type; ignore the other.
    }
  }
  return results;
}

async function validateTarget(url: URL): Promise<void> {
  if (url.protocol !== "https:") {
    throw new TargetValidationError("Only https URLs are allowed");
  }
  if (!isAllowedHost(url.hostname)) {
    throw new TargetValidationError(
      `Host '${url.hostname}' is not in the allowed hosts list`,
    );
  }
  const ips = await resolveHostIps(url.hostname);
  for (const ip of ips) {
    if (isPrivateIp(ip)) {
      throw new TargetValidationError(
        `Host '${url.hostname}' resolves to a private/internal IP (${ip})`,
      );
    }
  }
}

async function readBodyWithLimit(resp: Response, limitBytes: number): Promise<string> {
  if (!resp.body) return "";
  const reader = resp.body.getReader();
  const decoder = new TextDecoder();
  let total = 0;
  const chunks: Uint8Array[] = [];
  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    total += value.byteLength;
    if (total > limitBytes) {
      await reader.cancel();
      throw new Error(`Response body exceeds maximum size of ${limitBytes} bytes`);
    }
    chunks.push(value);
  }
  let text = "";
  for (const chunk of chunks) {
    text += decoder.decode(chunk, { stream: true });
  }
  return text + decoder.decode();
}

async function fetchHtml(targetUrl: string): Promise<string> {
  let currentUrl: URL;
  try {
    currentUrl = new URL(targetUrl);
  } catch {
    throw new TargetValidationError("Invalid URL");
  }
  await validateTarget(currentUrl);

  const userAgent = Deno.env.get("USER_AGENT");

  for (let redirectCount = 0; redirectCount <= MAX_REDIRECTS; redirectCount++) {
    const headers = new Headers();
    if (userAgent) {
      headers.set("User-Agent", userAgent);
    }
    const resp = await fetch(currentUrl, { headers, redirect: "manual" });

    if (resp.status >= 300 && resp.status < 400) {
      const location = resp.headers.get("location");
      await resp.body?.cancel();
      if (!location) {
        throw new Error("Redirect response without a Location header");
      }
      currentUrl = new URL(location, currentUrl);
      await validateTarget(currentUrl);
      continue;
    }

    if (!resp.ok) {
      await resp.body?.cancel();
      throw new Error(`Failed to fetch: ${resp.status} ${resp.statusText}`);
    }

    const source = await readBodyWithLimit(resp, MAX_FETCH_SIZE_BYTES);
    return source;
  }
  throw new Error("Too many redirects");
}

logger.info("Deno HTML fetcher API starting");

serve(async (req) => {
  const url = new URL(req.url);
  if (url.pathname === "/fetch") {
    const targetUrl = url.searchParams.get("url");
    if (!targetUrl) {
      return new Response("Missing 'url' query parameter", { status: 400 });
    }
    try {
      logger.info(`Fetching ${targetUrl}`);
      const source = await fetchHtml(targetUrl);
      return new Response(source, { headers: { "Content-Type": "text/html" } });
    } catch (e) {
      logger.error(`Error fetching URL: ${targetUrl}`, e);
      const message = e instanceof Error ? e.message : "Unexpected fetch error";
      const status = e instanceof TargetValidationError ? 400 : 500;
      return new Response(message, { status });
    }
  } else if (url.pathname === "/health") {
    return new Response("OK", { status: 200 });
  }
  return new Response("Not Found", { status: 404 });
}, { port: 8000 });

logger.info("Deno HTML fetcher API running on http://localhost:8000");
