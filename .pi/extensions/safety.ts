import type { ExtensionAPI } from "@earendil-works/pi-coding-agent";

const PROTECTED_PATHS = [
  /\.p8$/,
  /\/\.env$/,
  /\/\.env\./,
  /\/\.envrc$/,
  /^\.env$/,
  /^\.env\./,
  /^\.envrc$/,
  /\/secrets\//,
  /^secrets\//,
];

const BLOCKED_COMMANDS: Array<[RegExp, string]> = [
  [/convex\s+env/, "exposes environment secrets"],
  [/\bsudo\b/, "privilege escalation"],
  [/\bdoas\b/, "privilege escalation"],
  [/\b(mkfs|newfs|diskutil\s+erase)/, "disk format"],
  [/\bdd\s+.*\bof=\/dev\//, "raw disk write"],
  [/\b(chmod|chown)\s+-R\b/, "recursive permission change"],
  [/\b(shutdown|reboot|halt)\b/, "host power control"],
  [/\bkill\s+-9\s+-1\b/, "kill all processes"],
  [/:\(\)\s*\{\s*:\s*\|\s*:\s*&\s*\}\s*;/, "fork bomb"],
  [/\bgh\s+repo\s+delete\b/, "deletes a remote repository"],
  [/\bgit\s+push\b[^\n]*(--force|\s-f)(\s|$)/, "force-push"],
  [/\bgit\s+reset\b[^\n]*--hard\b/, "hard reset"],
  [/\bgit\s+clean\b[^\n]*-[a-zA-Z]*f/, "forced untracked delete"],
  [/\bgit\s+(filter-branch|filter-repo|update-ref)\b/, "history rewrite"],
  [/\brm\s+(-[a-zA-Z]*r[a-zA-Z]*f|-rf|-fr)\s+(\/|~|\$HOME)(\s|$|\/|\*)/, "recursive delete of root or home"],
];

function pathOf(input: Record<string, unknown>): string {
  const value = input.path ?? input.filePath ?? input.file_path;
  return typeof value === "string" ? value.replace(/\\/g, "/") : "";
}

export function isProtectedPath(filePath: string): boolean {
  const normalized = filePath.replace(/\\/g, "/");
  return PROTECTED_PATHS.some((pattern) => pattern.test(normalized));
}

export function blockedCommand(command: string): string | undefined {
  return BLOCKED_COMMANDS.find(([pattern]) => pattern.test(command))?.[1];
}

function blockReason(toolName: string, input: Record<string, unknown>): string | undefined {
  if (toolName === "read" || toolName === "write" || toolName === "edit") {
    const filePath = pathOf(input);
    if (filePath && isProtectedPath(filePath)) {
      return `protected file: ${filePath}`;
    }
  }
  if (toolName === "bash") {
    const command = typeof input.command === "string" ? input.command : "";
    const reason = command ? blockedCommand(command) : undefined;
    if (reason) return `${reason}: ${command}`;
  }
  return undefined;
}

export default function (pi: ExtensionAPI) {
  pi.on("tool_call", async (event) => {
    const reason = blockReason(event.toolName, event.input as Record<string, unknown>);
    if (reason) return { block: true, reason };
  });

  pi.on("user_bash", (event) => {
    const reason = blockedCommand(event.command);
    if (reason) {
      return {
        result: { output: `Blocked: ${reason}`, exitCode: 1, cancelled: false, truncated: false },
      };
    }
  });
}
