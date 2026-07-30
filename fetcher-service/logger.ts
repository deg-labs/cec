type LogLevel = "DEBUG" | "INFO" | "WARN" | "ERROR";

const minimumLevel = (Deno.env.get("LOG_LEVEL") ?? "INFO").toUpperCase() as LogLevel;
const priorities: Record<LogLevel, number> = { DEBUG: 10, INFO: 20, WARN: 30, ERROR: 40 };

function write(level: LogLevel, message: string, error?: unknown): void {
  if ((priorities[level] ?? priorities.INFO) < (priorities[minimumLevel] ?? priorities.INFO)) {
    return;
  }
  const detail = error instanceof Error ? { error: error.message, stack: error.stack } : error ? { error } : {};
  console[level === "ERROR" ? "error" : "log"](JSON.stringify({
    timestamp: new Date().toISOString(),
    level,
    message,
    ...detail,
  }));
}

export const logger = {
  info: (message: string) => write("INFO", message),
  error: (message: string, error?: unknown) => write("ERROR", message, error),
};
