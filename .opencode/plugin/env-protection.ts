/**
 * Environment, Secret & Host Protection Plugin
 *
 * Blocks OpenCode agents from:
 * - Reading sensitive files like .env, .p8, and secrets directories
 * - Running commands that could expose environment variables
 * - Running catastrophic commands that could damage the host or shared history
 *
 * This prevents accidental exposure of credentials, API keys, and private certificates.
 */

interface PluginContext {
  project: any;
  client: any;
  $: any;
  directory: any;
  worktree: any;
}

interface ToolInput {
  tool: string;
  [key: string]: any;
}

interface ToolOutput {
  args: {
    filePath?: string;
    file_path?: string;
    [key: string]: any;
  };
  [key: string]: any;
}

/**
 * Protected file patterns
 * Covers environment files, private keys, and secrets directories
 * Patterns match path segments ANYWHERE in the path (absolute or relative)
 */
const PROTECTED_FILE_PATTERNS = [
  // Private key files (.p8 extension anywhere)
  /\.p8$/,

  // Environment files (match /.env or /.env. anywhere in path)
  /\/\.env$/,           // Matches: /path/to/.env
  /\/\.env\./,          // Matches: /path/to/.env.local, .env.production, etc.
  /\/\.envrc$/,         // Matches: /path/to/.envrc

  // Catch relative paths at start (for ./. env, .env.local, etc.)
  /^\.env$/,            // Matches: .env (bare name)
  /^\.env\./,           // Matches: .env.local, .env.production (bare name with dot)
  /^\.envrc$/,          // Matches: .envrc (bare name)

  // Secrets directory (any file inside, absolute or relative)
  /\/secrets\//,        // Matches: /path/to/secrets/key.txt
  /^secrets\//,         // Matches: secrets/key.txt (relative)
];

/**
 * Protected command patterns
 * Blocks secret exposure and catastrophic, effectively irreversible operations
 */
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

/**
 * Check if a file path matches any protected patterns
 */
const isProtectedFile = (filePath: string): boolean => {
  const normalizedPath = filePath.replace(/\\/g, '/');
  return PROTECTED_FILE_PATTERNS.some(pattern => pattern.test(normalizedPath));
};

/**
 * Check if a command matches any protected patterns
 */
const protectedCommandReason = (command: string): string | undefined => {
  return PROTECTED_COMMAND_PATTERNS.find(([pattern]) => pattern.test(command))?.[1];
};

/**
 * Main plugin export
 */
export const EnvProtection = async (ctx: PluginContext) => {
  return {
    "tool.execute.before": async (input: ToolInput, output: ToolOutput) => {
      const toolName = input.tool.toLowerCase();

      // Block protected file reads
      if (toolName === "read") {
        const filePath = output.args.filePath || output.args.file_path;
        if (filePath && isProtectedFile(filePath)) {
          throw new Error(
            `🔒 PROTECTED FILE: Cannot read "${filePath}"\n` +
            `This file contains sensitive data (credentials, keys, or secrets).\n` +
            `Protected patterns: .env*, .p8, .envrc, secrets/`
          );
        }
      }

      // Block commands that expose environment secrets
      if (toolName === "bash") {
        const command = output.args.command;
        const reason = command ? protectedCommandReason(command) : undefined;
        if (reason) {
          throw new Error(
            `🔒 BLOCKED COMMAND: "${command}"\n` +
            `Reason: ${reason}.\n` +
            `This command is blocked by the environment and host safety policy.`
          );
        }
      }
    },
  };
};

// ============================================================================
// TEST CASES (for manual verification)
// ============================================================================
// Should BLOCK:
// - /workspace/playport-web/.env
// - /root/repo/.env.local
// - /Users/me/.env.production
// - .env
// - .env.development
// - .envrc
// - /workspace/playport-web/.envrc
// - /root/repo/secrets/api-key.txt
// - secrets/credentials.json
// - /path/to/auth-key.p8
// - app.p8
//
// Should ALLOW:
// - /workspace/playport-web/config.ts
// - src/env-utils.ts (contains "env" but not a protected file)
// - /path/to/notes.md
//
// COMMANDS - Should BLOCK:
// - convex env
// - npx convex env
// - bunx convex env
//
// COMMANDS - Should ALLOW:
// - convex dev
// - convex deploy
