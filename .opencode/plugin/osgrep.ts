/**
 * osgrep Server Lifecycle Plugin
 *
 * Manages the osgrep semantic search server lifecycle for OpenCode sessions.
 * - Uses `event` hook filtering for `session.created` event type
 * - Uses --parent-pid for auto-cleanup when OpenCode exits
 * - osgrep's internal chokidar handles file watching for index updates
 */

import fs from "fs";
import net from "net";
import path from "path";
import { spawn } from "child_process";

interface PluginContext {
  project: any;
  client: any;
  $: any;
  directory: string;
  worktree: string;
}

/**
 * Check if a process with given PID is still alive
 * Uses signal 0 which doesn't kill but checks existence
 */
function isPidAlive(pid: number): boolean {
  try {
    process.kill(pid, 0);
    return true;
  } catch {
    return false;
  }
}

/**
 * Get PID of running osgrep server from lockfile, if alive
 */
function getRunningPid(lockfilePath: string): number | null {
  if (!fs.existsSync(lockfilePath)) return null;

  try {
    const data = JSON.parse(fs.readFileSync(lockfilePath, "utf-8"));
    if (typeof data?.pid === "number" && isPidAlive(data.pid)) {
      return data.pid;
    }
  } catch {
    // Malformed lockfile, treat as no server running
  }

  return null;
}

/**
 * Clean up stale lockfile
 */
function cleanLockfile(lockfilePath: string): void {
  try {
    if (fs.existsSync(lockfilePath)) {
      fs.unlinkSync(lockfilePath);
    }
  } catch {
    // Silent fail - file may already be gone
  }
}

/**
 * Ensure .osgrep directory exists for lockfile
 */
function ensureOsgrepDir(directory: string): void {
  const osgrepDir = path.join(directory, ".osgrep");
  if (!fs.existsSync(osgrepDir)) {
    fs.mkdirSync(osgrepDir, { recursive: true });
  }
}

const OSGREP_PORT = 4444;

/**
 * Check if a port is already in use (fallback detection)
 * Handles edge cases where server runs but lockfile is missing
 */
function isPortInUse(port: number): Promise<boolean> {
  return new Promise((resolve) => {
    const socket = new net.Socket();
    socket.setTimeout(200);

    socket.on("connect", () => {
      socket.destroy();
      resolve(true); // Port in use
    });

    socket.on("timeout", () => {
      socket.destroy();
      resolve(false); // No response = port free
    });

    socket.on("error", () => {
      socket.destroy();
      resolve(false); // Connection refused = port free
    });

    socket.connect(port, "127.0.0.1");
  });
}

/**
 * Main plugin export
 */
export const OsgrepPlugin = async (ctx: PluginContext) => {
  const { directory } = ctx;

  const LOCKFILE = path.join(directory, ".osgrep", "server.json");

  /**
   * Ensure osgrep server is running
   * Checks lockfile + PID health, then port availability, spawns if needed
   */
  async function ensureServerRunning(): Promise<void> {
    // Primary check: lockfile with valid PID
    const existingPid = getRunningPid(LOCKFILE);
    if (existingPid) {
      return;
    }

    // Fallback check: port in use (handles missing lockfile edge case)
    if (await isPortInUse(OSGREP_PORT)) {
      return;
    }

    // Clean stale lockfile
    cleanLockfile(LOCKFILE);

    // Ensure directory exists
    ensureOsgrepDir(directory);

    // Spawn server with --parent-pid for auto-cleanup
    const logFd = fs.openSync("/tmp/osgrep.log", "a");
    const child = spawn(
      "osgrep",
      ["serve", "--parent-pid", String(process.pid)],
      {
        cwd: directory,
        detached: true,
        stdio: ["ignore", logFd, logFd],
      },
    );
    child.unref();

    // Write lockfile with PID for duplicate spawn prevention
    // Mirrors Claude Code hooks pattern where stop.js expects this file
    if (child.pid) {
      fs.writeFileSync(LOCKFILE, JSON.stringify({ pid: child.pid }));
    }
  }

  return {
    event: async ({ event }) => {
      if (event.type === "session.created") {
        try {
          await ensureServerRunning();
        } catch {
          // Silent fail - don't break OpenCode
        }
      }
    },
  };
};
