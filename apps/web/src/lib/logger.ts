type LogLevel = "debug" | "info" | "warn" | "error";

export interface LogFields {
  [key: string]: unknown;
}

const LEVEL_RANK: Record<LogLevel, number> = {
  debug: 10,
  info: 20,
  warn: 30,
  error: 40,
};

const sessionId = generateId("sess");
let minLevel: LogLevel =
  (import.meta.env.VITE_LOG_LEVEL as LogLevel | undefined) ??
  (import.meta.env.DEV ? "debug" : "info");

function generateId(prefix: string): string {
  const raw =
    typeof crypto !== "undefined" && crypto.randomUUID
      ? crypto.randomUUID().replace(/-/g, "").slice(0, 12)
      : Math.random().toString(36).slice(2, 14);
  return `${prefix}_${raw}`;
}

export function newRequestId(): string {
  return generateId("req");
}

export function getSessionId(): string {
  return sessionId;
}

export function setMinLevel(level: LogLevel): void {
  minLevel = level;
}

function shouldLog(level: LogLevel): boolean {
  return LEVEL_RANK[level] >= LEVEL_RANK[minLevel];
}

function emit(level: LogLevel, event: string, fields?: LogFields): void {
  if (!shouldLog(level)) return;
  const base = {
    ts: new Date().toISOString(),
    level,
    event,
    session_id: sessionId,
    ...fields,
  };
  const consoleFn =
    level === "error" ? console.error : level === "warn" ? console.warn : console.log;
  if (import.meta.env.DEV) {
    const tag = level.toUpperCase().padEnd(5);
    const extras = fields && Object.keys(fields).length > 0 ? fields : undefined;
    consoleFn(`%c${tag}%c ${event}`, styleFor(level), "color:inherit", extras ?? "");
  } else {
    consoleFn(JSON.stringify(base));
  }
}

function styleFor(level: LogLevel): string {
  switch (level) {
    case "debug":
      return "color:#6b7280;font-weight:500";
    case "info":
      return "color:#0ea5e9;font-weight:600";
    case "warn":
      return "color:#f59e0b;font-weight:600";
    case "error":
      return "color:#ef4444;font-weight:700";
  }
}

export const logger = {
  debug: (event: string, fields?: LogFields) => emit("debug", event, fields),
  info: (event: string, fields?: LogFields) => emit("info", event, fields),
  warn: (event: string, fields?: LogFields) => emit("warn", event, fields),
  error: (event: string, fields?: LogFields) => emit("error", event, fields),
};
