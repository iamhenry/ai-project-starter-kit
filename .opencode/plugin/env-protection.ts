/**
 * Environment & Secret File Protection Plugin
 *
 * Blocks OpenCode agents from:
 * - Reading sensitive files like .env, .p8, and secrets directories
 * - Running commands that could expose environment variables
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
 * Blocks CLI commands that could expose environment secrets
 */
const PROTECTED_COMMAND_PATTERNS = [
  /convex\s+env/,         // Matches: convex env, npx convex env, etc.
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
const isProtectedCommand = (command: string): boolean => {
  return PROTECTED_COMMAND_PATTERNS.some(pattern => pattern.test(command));
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
        if (command && isProtectedCommand(command)) {
          throw new Error(
            `🔒 BLOCKED COMMAND: "${command}"\n` +
            `This command could expose environment secrets.`
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
