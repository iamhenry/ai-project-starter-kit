/**
 * Reply budget: asks the model to keep its final reply under N characters of
 * prose before every agent-loop model call. It only adds an instruction; it
 * never truncates or rewrites a reply, so nothing is cut mid-thought.
 *
 * Change the limit with the OPENCODE_REPLY_MAX_CHARS env var (default 500).
 */
const MAX_CHARS = Number(process.env.OPENCODE_REPLY_MAX_CHARS) || 500;

const INSTRUCTION =
  `Reply budget: keep your final reply to the user under ${MAX_CHARS} characters of prose. ` +
  "Lead with the answer and any decision needed, and never omit critical information. " +
  "Diagrams, tables, code blocks and UI blocks do not count toward the limit. " +
  "This applies to the final reply only, not to tool calls or progress notes.";

// Plain object instead of Plugin.define(): define() is an identity helper, and
// skipping the "@opencode/plugin" import avoids a package-resolution failure.
export default {
  id: "reply-budget",
  async setup(ctx: any) {
    await ctx.session.hook("context", (event: any) => {
      event.system.push({ type: "text", text: INSTRUCTION });
    });
  },
};
