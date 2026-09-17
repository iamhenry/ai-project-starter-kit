export const meta = {
  name: "council",
  description: "Four specialist perspectives debate a hard question and synthesize agreement or dissent",
  inputSchema: {
    type: "object",
    required: ["query"],
    additionalProperties: false,
    properties: {
      query: { type: "string", minLength: 10 },
      maxRounds: { type: "integer", minimum: 1, maximum: 5 },
      consensusMode: { enum: ["unanimous", "majority"] },
      debug: { type: "boolean" },
    },
  },
  outputSchema: {
    type: "object",
    required: ["topic", "outcome", "rounds", "synthesis", "finalVoteSummary"],
    additionalProperties: false,
    properties: {
      topic: { type: "string" },
      outcome: { enum: ["consensus", "dissent"] },
      rounds: { type: "integer", minimum: 1, maximum: 5 },
      synthesis: { type: "string" },
      finalVoteSummary: {
        type: "object",
        required: ["mode", "accepts", "rejects", "total"],
        additionalProperties: false,
        properties: {
          mode: { enum: ["unanimous", "majority"] },
          accepts: { type: "integer", minimum: 0, maximum: 4 },
          rejects: { type: "integer", minimum: 0, maximum: 4 },
          total: { type: "integer", minimum: 0, maximum: 4 },
        },
      },
      transcript: {
        type: "array",
        items: {
          type: "object",
          required: ["kind", "role", "round", "content"],
          additionalProperties: false,
          properties: {
            kind: { enum: ["opening", "response", "proposal", "vote", "system"] },
            role: { enum: ["researcher", "logician", "creative", "critic", "synthesizer"] },
            round: { type: "integer", minimum: 0, maximum: 5 },
            content: { type: "string" },
          },
        },
      },
    },
  },
  phases: [
    { title: "Openings", detail: "Four independent specialist positions" },
    { title: "Proposal", detail: "One rotating proposer drafts a resolution" },
    { title: "Votes", detail: "Four independent acceptance votes" },
    { title: "Revisions", detail: "Rejected positions are refreshed before the next round" },
    { title: "Synthesis", detail: "The full transcript becomes an honest final answer" },
  ],
};

/*
 * Ported from RoderickOxen/opencode-council at commit
 * 066b2add1c831d5ba1843695171c72879edb2d45.
 * Copyright (c) 2026 RoderickOxen. MIT; see README.md for the notice.
 */

// BEGIN deterministic protocol helpers
const ROLE_ORDER = ["researcher", "logician", "creative", "critic"];

function proposerForRound(round) {
  return ROLE_ORDER[(round - 1) % ROLE_ORDER.length];
}

function evaluateVotes(votes, round, maxRounds, consensusMode) {
  let accepts = 0;
  for (const vote of votes) {
    if (vote.decision === "accept") accepts += 1;
  }
  const consensus = consensusMode === "unanimous"
    ? accepts === votes.length
    : accepts > votes.length / 2;
  if (consensus) return "consensus";
  return round >= maxRounds ? "dissent" : "proposing";
}

function fallbackPosition(role) {
  return { role, summary: "[no response]", keyPoints: [], openQuestion: "" };
}

function fallbackProposal(proposerRole, round) {
  return {
    proposerRole,
    round,
    resolution: "[no proposal]",
    rationale: "",
    tradeoffs: "",
  };
}

function fallbackVote(role) {
  return { role, decision: "reject", reason: "[no response]", concession: "" };
}

function fallbackSynthesis() {
  return "[synthesis unavailable]";
}

function transcriptEntry(kind, role, round, content) {
  return { kind, role, round, content };
}

function summarizeVotes(votes, consensusMode) {
  let accepts = 0;
  for (const vote of votes) {
    if (vote.decision === "accept") accepts += 1;
  }
  return {
    mode: consensusMode,
    accepts,
    rejects: votes.length - accepts,
    total: votes.length,
  };
}
// END deterministic protocol helpers

const DEFAULT_MAX_ROUNDS = 3;
const DEFAULT_CONSENSUS_MODE = "unanimous";

const ROLE_CONFIG = {
  researcher: {
    label: "Researcher",
    persona: "Research Specialist",
    mandate: "Provide accurate, evidence-based analysis. Distinguish what is empirically known from what is assumed or speculated. Cite concrete evidence, historical analogues, or documented precedents.",
    acceptanceBar: "Reject claims that lack verifiable evidence, falsifiable criteria, or a way to confirm the promised outcome. Flag unverified assumptions explicitly.",
    systemPrompt: "You are the Research Specialist on a multi-agent deliberative council that reasons through hard questions. Your council considers questions across any domain — ethics, strategy, policy, science, design, or any other area of genuine difficulty.\n\nYour mandate: provide accurate, evidence-based analysis. Distinguish what is empirically known from what is assumed or speculated. Cite concrete evidence, historical analogues, or documented precedents wherever possible.\n\nYour acceptance bar: reject claims that lack verifiable evidence, falsifiable criteria, or a way to confirm the promised outcome. Flag unverified assumptions explicitly.\n\nIn each round, identify what is actually known versus assumed, surface the most important empirical question left open, and challenge overconfident claims regardless of which direction they lean.",
  },
  logician: {
    label: "Logician",
    persona: "Logic and Reasoning Specialist",
    mandate: "Provide rigorous logical analysis, identify edge cases, check internal consistency, and evaluate whether conclusions actually follow from the premises. Surface the sharpest counterexample.",
    acceptanceBar: "Reject arguments that contain logical fallacies, ignore stated constraints, paper over edge cases, or whose conclusions do not follow from their premises.",
    systemPrompt: "You are the Logic and Reasoning Specialist on a multi-agent deliberative council that reasons through hard questions. Your council considers questions across any domain — ethics, strategy, policy, science, design, or any other area of genuine difficulty.\n\nYour mandate: provide rigorous logical analysis, identify edge cases, check internal consistency, and evaluate whether conclusions actually follow from the premises. Surface the sharpest counterexample to any position.\n\nYour acceptance bar: reject arguments that contain logical fallacies, ignore stated constraints, paper over edge cases, or whose conclusions do not follow from their premises.\n\nIn each round, check: does the reasoning hold under the stated assumptions? What is the strongest counterexample? Under what conditions does this argument fail?",
  },
  creative: {
    label: "Creative",
    persona: "Creative Strategist",
    mandate: "Challenge the dominant framing. Offer alternative problem definitions, unconventional approaches, and surface second-order effects and human impact that the other perspectives may overlook.",
    acceptanceBar: "Reject solutions that are technically correct but ignore human factors, assume the current problem framing is the only valid one, or fail to account for second-order consequences.",
    systemPrompt: "You are the Creative Strategist on a multi-agent deliberative council that reasons through hard questions. Your council considers questions across any domain — ethics, strategy, policy, science, design, or any other area of genuine difficulty.\n\nYour mandate: challenge the dominant framing. Offer alternative problem definitions, unconventional approaches, and surface second-order effects and human impact that the other perspectives may overlook.\n\nYour acceptance bar: reject solutions that are technically correct but ignore human factors, assume the current problem framing is the only valid one, or fail to account for second-order consequences.\n\nIn each round, offer at least one reframing of the question itself, name one non-obvious consequence of the proposed direction, and identify what is being left out of the current conversation.",
  },
  critic: {
    label: "Critic",
    persona: "Critical Analyst",
    mandate: "Identify weaknesses, risks, and blind spots. Play devil's advocate. Accept a proposal only when you genuinely cannot find a credible objection — not when it merely sounds reasonable.",
    acceptanceBar: "Reject arguments that paper over risks, overstate confidence, lack a credible failure model, or rely on assumptions that have not been stress-tested.",
    systemPrompt: "You are the Critical Analyst on a multi-agent deliberative council that reasons through hard questions. Your council considers questions across any domain — ethics, strategy, policy, science, design, or any other area of genuine difficulty.\n\nYour mandate: identify weaknesses, risks, and blind spots. Play devil's advocate. Your role is NOT to be contrarian for its own sake — it is to surface the objections that the other perspectives are not raising.\n\nYour acceptance bar: reject arguments that paper over risks, overstate confidence, lack a credible failure model, or rely on assumptions that have not been stress-tested. Accept only when you genuinely cannot find a credible objection.\n\nIn each round, name the single most dangerous assumption in the proposal, describe the scenario under which it most plausibly fails, and state the minimum change that would address your concern.",
  },
};

const SYNTHESIZER_SYSTEM_PROMPT = "You are the Synthesizer on a multi-agent deliberative council. You do NOT take sides or advocate for any position. Your role is to produce a clear, honest final answer after the council has deliberated.\n\nYour synthesis must cover:\n1. The council's best answer to the question — concrete and actionable, not evasive\n2. Points of genuine agreement across the four specialist perspectives\n3. Unresolved tensions and genuine disagreements that remain after debate\n4. The most important caveat or open question the user should keep in mind\n\nDo not flatten disagreements into false consensus. If the council is genuinely divided, say so and explain why. Your synthesis is shown directly to the user — make it worth reading.";

const POSITION_SCHEMA = {
  type: "object",
  required: ["summary", "keyPoints", "openQuestion"],
  additionalProperties: false,
  properties: {
    summary: { type: "string" },
    keyPoints: { type: "array", minItems: 3, items: { type: "string" } },
    openQuestion: { type: "string" },
  },
};

const PROPOSAL_SCHEMA = {
  type: "object",
  required: ["resolution", "rationale", "tradeoffs"],
  additionalProperties: false,
  properties: {
    resolution: { type: "string" },
    rationale: { type: "string" },
    tradeoffs: { type: "string" },
  },
};

const VOTE_SCHEMA = {
  type: "object",
  required: ["decision", "reason", "concession"],
  additionalProperties: false,
  properties: {
    decision: { enum: ["accept", "reject"] },
    reason: { type: "string" },
    concession: { type: "string" },
  },
};

const SYNTHESIS_SCHEMA = {
  type: "object",
  required: ["synthesis"],
  additionalProperties: false,
  properties: { synthesis: { type: "string" } },
};

function normaliseArgs(input) {
  const value = input && typeof input === "object" ? input : {};
  const maxRounds = Number.isInteger(value.maxRounds) && value.maxRounds >= 1 && value.maxRounds <= 5
    ? value.maxRounds
    : DEFAULT_MAX_ROUNDS;
  return {
    topic: typeof value.query === "string" ? value.query : "[no question]",
    maxRounds,
    consensusMode: value.consensusMode === "majority" ? "majority" : DEFAULT_CONSENSUS_MODE,
    debug: value.debug === true,
  };
}

function roleInstruction(role) {
  const config = ROLE_CONFIG[role];
  return `${config.systemPrompt}\n\nYour mandate: ${config.mandate}\nYour acceptance bar: ${config.acceptanceBar}\n\nYou may inspect the codebase and consult the web when useful. Do not create, edit, delete, or otherwise write files. Return only the structured result requested below.`;
}

function positionSummary(positions) {
  return ROLE_ORDER.map((role) => {
    const position = positions.find((item) => item.role === role) || fallbackPosition(role);
    return `[${role}]: ${position.summary}\nKey points: ${position.keyPoints.join("; ")}\nOpen question: ${position.openQuestion}`;
  }).join("\n");
}

function detailedPositionSummary(positions) {
  return ROLE_ORDER.map((role) => {
    const position = positions.find((item) => item.role === role) || fallbackPosition(role);
    return `[${role}]: ${position.summary}\nKey points: ${position.keyPoints.join("; ")}`;
  }).join("\n\n");
}

function voteSummary(votes) {
  return votes.map((vote) => `[${vote.role}]: ${vote.decision} — ${vote.reason}`).join("\n");
}

function allPriorVotes(voteSets) {
  const votes = [];
  for (const voteSet of voteSets) {
    for (const vote of voteSet) votes.push(vote);
  }
  return votes.length > 0
    ? `\nPrior votes:\n${voteSummary(votes)}`
    : "";
}

function buildOpeningPrompt(topic, role) {
  return `${roleInstruction(role)}\n\nCouncil question: ${topic}\n\nThis is the opening round. Provide your initial analysis through your specialist lens. Surface a concrete tension or open question — do not default to false balance.\n\nReturn an object with:\n{\n  "summary": "<under 90 words>",\n  "keyPoints": ["<string>", "<string>", "<string>"],\n  "openQuestion": "<the most important question left open>"\n}`;
}

function buildResponsePrompt(topic, role, round, positions, proposal, votes) {
  const config = ROLE_CONFIG[role];
  return `${roleInstruction(role)}\n\nCouncil question: ${topic}\n\nRound ${round}. You are the ${config.persona}.\n\nAll positions from the previous round:\n${positionSummary(positions)}\n\nProposal on the table:\n"${proposal.resolution}"\n\nVotes cast:\n${voteSummary(votes)}\n\nRespond through your specialist lens. Has the proposal resolved your concerns? Identify what still needs to change to meet your acceptance bar.\n\nReturn an object with:\n{\n  "summary": "<under 90 words>",\n  "keyPoints": ["<string>", "<string>", "<string>"],\n  "openQuestion": "<the most important question still unresolved for you>"\n}`;
}

function buildProposalPrompt(topic, role, round, positions, proposals, voteSets) {
  const config = ROLE_CONFIG[role];
  const priorProposals = proposals.length > 0
    ? `\nPrior proposals:\n${proposals.map((proposal) => `[Round ${proposal.round}][${proposal.proposerRole}]: ${proposal.resolution}\nRationale: ${proposal.rationale}\nTrade-offs: ${proposal.tradeoffs}`).join("\n")}`
    : "";
  return `${roleInstruction(role)}\n\nCouncil question: ${topic}\n\nRound ${round}. You are the ${config.persona} and the designated proposer this round.\n\nAll council positions:\n${detailedPositionSummary(positions)}${priorProposals}${allPriorVotes(voteSets)}\n\nDraft a concrete resolution that addresses the most important concerns from all perspectives. Make an explicit choice. Do not hide trade-offs.\n\nReturn an object with:\n{\n  "resolution": "<under 120 words — a concrete, actionable answer>",\n  "rationale": "<under 70 words>",\n  "tradeoffs": "<explicit trade-offs you are accepting>"\n}`;
}

function buildVotePrompt(topic, role, round, proposal, positions) {
  const config = ROLE_CONFIG[role];
  const position = positions.find((item) => item.role === role) || fallbackPosition(role);
  return `${roleInstruction(role)}\n\nCouncil question: ${topic}\n\nRound ${round}. You are the ${config.persona}.\n\nYour latest position:\nSummary: ${position.summary}\nKey points: ${position.keyPoints.join("; ")}\nOpen question: ${position.openQuestion}\n\nProposal on the table:\n"${proposal.resolution}"\nRationale: ${proposal.rationale}\nTrade-offs acknowledged: ${proposal.tradeoffs}\n\nVote independently. Accept ONLY if this proposal explicitly satisfies your acceptance bar and resolves the material concerns in your latest position. Otherwise reject and name the smallest change that would make it acceptable.\n\nReturn an object with decision set to "accept" or "reject":\n{\n  "decision": "accept",\n  "reason": "<under 55 words>",\n  "concession": "<one point you genuinely learned from another perspective, or empty string>"\n}`;
}

function buildSynthesisPrompt(topic, outcome, rounds, transcript) {
  const transcriptText = transcript
    .map((entry) => `[Round ${entry.round}][${entry.role}][${entry.kind}]: ${entry.content}`)
    .join("\n");
  return `${SYNTHESIZER_SYSTEM_PROMPT}\n\nYou may inspect the codebase and consult the web when useful, but do not create, edit, delete, or otherwise write files.\n\nCouncil question: ${topic}\n\nThe debate concluded with ${outcome} after ${rounds} round${rounds === 1 ? "" : "s"}.\n\nFull deliberation transcript:\n${transcriptText || "(no transcript entries)"}\n\nSynthesize the council's deliberation. Produce a response covering:\n1. The council's best answer to the question\n2. Points of genuine agreement across perspectives\n3. Unresolved tensions that remain\n4. The most important caveat or open question going forward\n\nBe concrete. Do not evade the hard parts. Return an object with a single "synthesis" string. Do not flatten disagreements into false consensus.`;
}

async function callWorker(prompt, role, label, phaseName, schema, fallback) {
  try {
    const result = await agent(prompt, {
      label,
      phase: phaseName,
      schema,
      // Edit these three literals together when changing the council model.
      provider: "opencode",
      model: "openai/gpt-5.6-luna",
      reasoningLevel: "low",
    });
    return result || fallback;
  } catch (_) {
    return fallback;
  }
}

function positionForRole(role, value) {
  const position = value || fallbackPosition(role);
  return {
    role,
    summary: position.summary,
    keyPoints: position.keyPoints,
    openQuestion: position.openQuestion,
  };
}

function proposalForRound(proposerRole, round, value) {
  const proposal = value || fallbackProposal(proposerRole, round);
  return {
    proposerRole,
    round,
    resolution: proposal.resolution,
    rationale: proposal.rationale,
    tradeoffs: proposal.tradeoffs,
  };
}

function voteForRole(role, value) {
  const vote = value || fallbackVote(role);
  return {
    role,
    decision: vote.decision,
    reason: vote.reason,
    concession: vote.concession,
  };
}

const input = normaliseArgs(args);
const { topic, maxRounds, consensusMode, debug } = input;
const transcript = [];

phase("Openings");
const openingResults = await parallel(
  ROLE_ORDER.map((role) => () => callWorker(
    buildOpeningPrompt(topic, role),
    role,
    `Openings · ${ROLE_CONFIG[role].label} · opening analysis`,
    "Openings",
    POSITION_SCHEMA,
    fallbackPosition(role),
  )),
);

let positions = ROLE_ORDER.map((role, index) => {
  const position = positionForRole(role, openingResults[index]);
  transcript.push(transcriptEntry("opening", role, 0, JSON.stringify(position)));
  return position;
});

let outcome = "dissent";
let finalRound = 0;
let finalVotes = [];
const proposals = [];
const voteSets = [];

for (let round = 1; round <= maxRounds; round += 1) {
  finalRound = round;
  const proposerRole = proposerForRound(round);

  phase("Proposal");
  const rawProposal = await callWorker(
    buildProposalPrompt(topic, proposerRole, round, positions, proposals, voteSets),
    proposerRole,
    `Proposal · ${ROLE_CONFIG[proposerRole].label} · round ${round}`,
    "Proposal",
    PROPOSAL_SCHEMA,
    fallbackProposal(proposerRole, round),
  );
  const proposal = proposalForRound(proposerRole, round, rawProposal);
  proposals.push(proposal);
  transcript.push(transcriptEntry("proposal", proposerRole, round, JSON.stringify(proposal)));

  phase("Votes");
  const voteResults = await parallel(
    ROLE_ORDER.map((role) => () => callWorker(
      buildVotePrompt(topic, role, round, proposal, positions),
      role,
      `Votes · ${ROLE_CONFIG[role].label} · round ${round}`,
      "Votes",
      VOTE_SCHEMA,
      fallbackVote(role),
    )),
  );
  const votes = ROLE_ORDER.map((role, index) => {
    const vote = voteForRole(role, voteResults[index]);
    transcript.push(transcriptEntry("vote", role, round, JSON.stringify(vote)));
    return vote;
  });
  voteSets.push(votes);
  finalVotes = votes;

  const evaluation = evaluateVotes(votes, round, maxRounds, consensusMode);
  if (evaluation === "consensus") {
    outcome = "consensus";
    break;
  }
  if (evaluation === "dissent") break;

  phase("Revisions");
  const responseResults = await parallel(
    ROLE_ORDER.map((role) => () => callWorker(
      buildResponsePrompt(topic, role, round, positions, proposal, votes),
      role,
      `Revisions · ${ROLE_CONFIG[role].label} · round ${round}`,
      "Revisions",
      POSITION_SCHEMA,
      fallbackPosition(role),
    )),
  );
  positions = ROLE_ORDER.map((role, index) => {
    const position = positionForRole(role, responseResults[index]);
    transcript.push(transcriptEntry("response", role, round, JSON.stringify(position)));
    return position;
  });
}

phase("Synthesis");
const synthesisResult = await callWorker(
  buildSynthesisPrompt(topic, outcome, finalRound, transcript),
  "synthesizer",
  "Synthesis · Synthesizer · final synthesis",
  "Synthesis",
  SYNTHESIS_SCHEMA,
  { synthesis: fallbackSynthesis() },
);
const synthesis = synthesisResult.synthesis || fallbackSynthesis();
transcript.push(transcriptEntry("system", "synthesizer", finalRound, synthesis));

const result = {
  topic,
  outcome,
  rounds: finalRound,
  synthesis,
  finalVoteSummary: summarizeVotes(finalVotes, consensusMode),
};
if (debug) {
  result.transcript = transcript;
}
return result;
