import { Plugin } from "@opencode/plugin";

/**
 * Environment, secret, and host protection for OpenCode V2.
 *
 * Blocks sensitive file reads, secret-dumping commands, and a small set of
 * catastrophic host or shared-history operations before a tool can run.
 */

const PROTECTED_FILE_PATTERNS = [
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

const PROTECTED_COMMAND_PATTERNS: Array<[RegExp, string]> = [
  [/convex\s+env/, "exposes environment secrets"],
  [/(?:^|[;&|]\s*)printenv\b/, "dumps environment secrets"],
  [/(?:^|[;&|]\s*)env\s*(?:$|[|;])/, "dumps environment secrets"],
  [/(?:^|[;&|]\s*)export\s+-p\b/, "dumps environment secrets"],
  [/(?:^|[;&|]\s*)set\s*(?:$|[|;])/, "dumps shell variables"],
  [/\b(?:sudo|doas)\b/, "attempts privilege escalation"],
  [/\b(?:mkfs(?:\.[\w+-]+)?|newfs(?:_[\w+-]+)?)\b/i, "formats a filesystem"],
  [/\bdiskutil\s+(?:eraseDisk|eraseVolume|partitionDisk|secureErase|zeroDisk|randomDisk)\b/i, "erases or repartitions a disk"],
  [/\bdiskutil\s+apfs\s+(?:deleteContainer|deleteVolume|eraseVolume)\b/i, "deletes or erases an APFS container or volume"],
  [/\bdd\b[^;&|\n]*\bof\s*=\s*["']?\/dev\//i, "writes directly to a device"],
  [/\b(?:fdisk|gpt)\b[^;&|\n]*(?:destroy|remove|write)\b/i, "modifies a disk partition table"],
  [/\brm\b(?=[^;&|\n]*(?:-[a-zA-Z]*[rR]|--recursive))(?=[^;&|\n]*(?:-[a-zA-Z]*f|--force))[^;&|\n]*\s["']?(?:\/|~|\$HOME)(?:["']?(?:\s|$)|\/|\*)/, "recursively deletes root or the home directory"],
  [/\b(?:chmod|chown)\b(?=[^;&|\n]*(?:-R|--recursive))[^;&|\n]*\s["']?(?:\/|~|\$HOME)(?:["']?(?:\s|$)|\/|\*)/, "recursively changes root or home permissions"],
  [/\b(?:shutdown|reboot|halt)\b/, "controls host power"],
  [/\bkill\s+-9\s+-1\b/, "kills all accessible processes"],
  [/:\(\)\s*\{\s*:\s*\|\s*:\s*&\s*\}\s*;/, "starts a fork bomb"],
  [/\bgh\s+repo\s+delete\b/, "deletes a remote repository"],
  [/\bgit\b[^;&|\n]*\bpush\b[^;&|\n]*(?:--force(?:-with-lease|-if-includes)?(?:=|\s|$)|(?:^|\s)-[a-zA-Z]*f[a-zA-Z]*(?:\s|$))/, "force-pushes shared history"],
  [/\bgit\b[^;&|\n]*\b(?:filter-branch|filter-repo)\b/, "rewrites repository history"],
  [/\bgit\b[^;&|\n]*\bupdate-ref\b[^;&|\n]*(?:\s-d(?:\s|$)|--delete(?:\s|$))/, "deletes a Git reference"],
];

const isProtectedFile = (filePath: string): boolean => {
  const normalizedPath = filePath.replace(/\\/g, "/");
  return PROTECTED_FILE_PATTERNS.some((pattern) => pattern.test(normalizedPath));
};

const protectedCommandReason = (command: string): string | undefined =>
  PROTECTED_COMMAND_PATTERNS.find(([pattern]) => pattern.test(command))?.[1];

export default Plugin.define({
  id: "env-protection",
  async setup(ctx) {
    await ctx.tool.hook("execute.before", (event) => {
      const toolName = event.tool.toLowerCase();
      const input = event.input as Record<string, unknown>;

      if (toolName === "read") {
        const filePath = input.filePath ?? input.file_path ?? input.path;
        if (typeof filePath === "string" && isProtectedFile(filePath)) {
          throw new Error(
            `🔒 PROTECTED FILE: Cannot read "${filePath}"\n` +
              "This file contains sensitive data (credentials, keys, or secrets).\n" +
              "Protected patterns: .env*, .p8, .envrc, secrets/",
          );
        }
      }

      if (toolName === "shell" || toolName === "bash") {
        const command = input.command;
        const reason =
          typeof command === "string" ? protectedCommandReason(command) : undefined;
        if (reason) {
          throw new Error(
            `🔒 BLOCKED COMMAND: "${command}"\n` +
              `Reason: ${reason}.\n` +
              "This command is blocked by the environment and host safety policy.",
          );
        }
      }
    });
  },
});
