# SOFTWARE ETHOS

This doc captures the ethos and philosophy on how I prefer to make product and technical decisions so other people and AI agents can align with me across projects.

The goal is PRAGMATIC, REDUCE FRICTION, SIMPLE, USER‑TRUST‑FOCUSED decisions, not rigid rules.

---

## CORE PRINCIPLES

Organized by decision domain: WHY → HOW → WHO

### STRATEGY (Why we build)

1) TRACER BULLET FIRST  
- IDEA: Ship the smallest version that proves the full flow end to end. Improve after it works.  
- EXAMPLE: Build basic connect → select → start flow with minimal states, then refine visuals and edge cases later.  
- HEURISTIC QUESTION: WHAT IS THE SIMPLEST THING THAT PROVES THIS FLOW WORKS FOR A REAL USER?

2) USE MATURE LIBRARIES FOR TRICKY LOGIC  
- IDEA: For fuzzy matching, ranking, or other subtle logic, lean toward stable libraries instead of re‑inventing algorithms.  
- EXAMPLE: Use a well‑tested matching library for comparing song titles instead of writing a custom string distance from scratch.  
- HEURISTIC QUESTION: IS THERE A WELL‑KNOWN LIBRARY THAT HANDLES 80 PERCENT OF THIS SAFER THAN MY CUSTOM CODE?

3) START TIGHT, LOOSEN WITH EVIDENCE  
- IDEA: Begin with conservative defaults and constraints. Relax them only when real usage data proves the need.  
- EXAMPLE: Launch with strict rate limits or feature flags disabled; enable broader access after observing actual user behavior.  
- HEURISTIC QUESTION: AM I ADDING FLEXIBILITY BECAUSE USERS NEED IT, OR BECAUSE I MIGHT NEED IT SOMEDAY?

4) USER IN CONTROL  
- IDEA: Users should always be able to undo/reverse actions and move at their own pace without being forced through flows.  
- EXAMPLE: Allow canceling a transfer mid-progress, stepping back in a multi-step wizard without losing work, or undoing a deletion.  
- HEURISTIC QUESTION: CAN THE USER REVERSE THIS ACTION OR EXIT THIS FLOW WITHOUT LOSING PROGRESS?

### ARCHITECTURE (How we structure)

5) REUSE EXISTING PIECES BEFORE ADDING NEW ONES  
- IDEA: Prefer to reuse existing components, queries, and flows instead of inventing new state or surfaces.  
- EXAMPLE: Use an existing "connect" button and existing status query instead of adding new local storage or one‑off flags.  
- HEURISTIC QUESTION: CAN I EXPRESS THIS BEHAVIOR USING WHAT I ALREADY HAVE IN THE SYSTEM?

6) ONE FACT, ONE PLACE  
- IDEA: Store each piece of data once and derive everything else on read. Duplication creates drift between sources.  
- EXAMPLE: Store track statuses individually; compute progress counts on read rather than maintaining a separate counter that can get out of sync.  
- HEURISTIC QUESTION: IF I UPDATE THIS VALUE, WILL I NEED TO UPDATE IT IN MULTIPLE PLACES TO STAY CONSISTENT?

7) SECURITY AND PRIVACY OVER DEBUG CONVENIENCE  
- IDEA: Never leak secrets or personal data just to make debugging easier.  
- EXAMPLE: Log events and ids in a safe way, but never log tokens, emails, or other sensitive information.  
- HEURISTIC QUESTION: COULD THIS LOG OR DATA STORE EVER CONTAIN A TOKEN OR PERSONAL DETAIL IF SOMETHING GOES WRONG?

8) FAIL SAFELY, RECOVER QUICKLY  
- IDEA: Prefer graceful degradation over rigid correctness that crashes. Systems should bend, not break.  
- EXAMPLE: If a single track fails to transfer, continue with the rest and report partial success rather than aborting the entire job.  
- HEURISTIC QUESTION: IF THIS OPERATION FAILS, DOES THE USER LOSE ALL PROGRESS OR JUST THIS ONE STEP?

### EXECUTION (How we ship)

9) PRAGMATISM OVER PERFECTION  
- IDEA: Especially early, choose the option that is easiest to ship and reason about, as long as it does not clearly harm users or trust.  
- EXAMPLE: Defer non‑essential features to a later milestone and capture them in a roadmap instead of shipping everything at once.  
- HEURISTIC QUESTION: IS THIS NICE TO HAVE OR TRULY BLOCKING FOR USERS RIGHT NOW?

10) FEWER TRIPS, MORE CARGO  
- IDEA: Batch operations and parallelize where possible. Minimize round trips between client and server or between services.  
- EXAMPLE: Fetch all playlist tracks in one paginated call rather than fetching each track individually; add tracks to Spotify in batches of 100.  
- HEURISTIC QUESTION: CAN I COMBINE THESE SEPARATE CALLS INTO ONE, OR RUN THEM IN PARALLEL?

11) IDIOMATIC FIRST  
- IDEA: Write code that "belongs" in its ecosystem. Prefer the common, expected patterns of the language + framework + this repo over clever abstractions.  
- EXAMPLE: In React, keep state minimal and derive values instead of adding extra state. In Convex, keep server logic in queries/mutations/actions instead of hiding it in client helpers. In TypeScript, model real shapes (avoid any and vague "data" objects).  
- HEURISTIC QUESTION: IF A STRANGER WHO KNOWS THIS STACK READS THIS, WOULD THEY SAY "YEP, THAT'S HOW YOU DO IT HERE," OR "WHY DID THEY INVENT THEIR OWN WAY"?

### INTERACTION (Who we serve)

12) SIMPLE UX, FEWER STATES  
- IDEA: Prefer fewer, clearer states over many subtle ones. Label things so a non‑technical person understands them in seconds.  
- EXAMPLE: Use a single clear badge or status instead of multiple overlapping badges that might confuse users.  
- HEURISTIC QUESTION: COULD A NEW USER EXPLAIN THIS STATUS OR LABEL BACK TO ME IN ONE SENTENCE?

13) MINIMIZE FRICTION  
- IDEA: Good UX reduces effort to complete actions. Fewer clicks, simpler flows, less cognitive load = less frustration.  
- EXAMPLE: Shopping cart - add/remove/modify items with minimal clicks, no unnecessary confirmations or page reloads.  
- HEURISTIC QUESTION: CAN THE USER COMPLETE THIS ACTION WITH FEWER STEPS WHILE STILL FEELING IN CONTROL?

14) ANIMATE FOR MEANING  
- IDEA: Motion should guide user attention and communicate state changes, not decorate or delay. Every animation needs a purpose.  
- EXAMPLE: Animate a floating bar on first appearance to draw attention, but swap content instantly on subsequent updates to avoid feeling sluggish.  
- HEURISTIC QUESTION: DOES THIS ANIMATION HELP THE USER UNDERSTAND WHAT CHANGED, OR IS IT JUST VISUAL FLAIR?

15) PROTECT USER TRUST, EVEN AT THE COST OF FEATURES  
- IDEA: Avoid behavior that can silently betray user expectations, even if it looks smart on paper.  
- EXAMPLE: Be very careful about auto‑matching or auto‑changing items; a wrong result is worse than asking the user to confirm.  
- HEURISTIC QUESTION: IF THIS IS WRONG FOR 1 OUT OF 10 USERS, WILL THEY FEEL MISLED OR LOSE TRUST?

---

## ROADMAP PHASE HEURISTICS

PHASE 1: TRACER BULLET / PROOF  
- GOAL: Prove the main flow works for a single realistic scenario.  
- TESTS: OK TO DEFER, BUT TRY TO ADD AT LEAST ONE HAPPY PATH TEST FOR THE MOST CRITICAL FLOW WHEN POSSIBLE.  
- PERFORMANCE: CHOOSE THE SIMPLEST APPROACH, EVEN IF NOT PERFECTLY OPTIMIZED.  
- ERROR UX: BASIC ERROR HANDLING AND CONSOLE LOGS ARE OK, AS LONG AS THEY ARE SAFE AND DO NOT LEAK SENSITIVE DATA.

PHASE 2: BUILD OUT  
- GOAL: Cover more real‑world scenarios, reduce obvious rough edges.  
- TESTS: ADD HAPPY PATH TESTS FOR EACH CRITICAL FLOW; DEFERRING EDGE CASE TESTS IS OK.  
- PERFORMANCE: START FIXING CLEAR BOTTLENECKS USERS WOULD NOTICE; STILL AVOID HEAVY COMPLEXITY UNLESS NEEDED.  
- ERROR UX: UPGRADE FROM RAW ERRORS TO CLEAR, HUMAN‑READABLE MESSAGES FOR COMMON FAILURE CASES.

PHASE 3: POLISH AND HARDENING  
- GOAL: REFINE EXPERIENCE, REDUCE SURPRISES, AND MAKE THE SYSTEM FEEL TRUSTWORTHY.  
- TESTS: CRITICAL FLOWS SHOULD HAVE AT LEAST ONE AUTOMATED TEST EACH; ADD TARGETED EDGE CASE TESTS WHERE RISK IS HIGH.  
- PERFORMANCE: OK TO ADD CACHING OR MORE COMPLEX BEHAVIOR IF IT CLEARLY IMPROVES USER EXPERIENCE.  
- ERROR UX: MOST USER‑FACING FAILURES SHOULD HAVE CLEAR, ACTIONABLE MESSAGES IN THE UI, NOT JUST LOGS.

HEURISTIC QUESTION FOR EVERY DECISION:  
WHAT ROADMAP PHASE AM I IN RIGHT NOW, AND DOES THIS DECISION MATCH THAT PHASE?

---

## SOCRATIC QUESTIONS CHECKLIST

FOR ANY NEW FEATURE OR CHANGE, ASK:

1) VALUE AND SCOPE  
- WHAT IS THE SMALLEST VERSION OF THIS FEATURE THAT GIVES REAL VALUE TO A USER?  
- AM I ADDING ANYTHING THAT CAN SAFELY LIVE IN A LATER MILESTONE OR ROADMAP NOTE?

2) USER CLARITY  
- WILL A NEW USER UNDERSTAND WHAT IS HAPPENING WITHOUT READING DOCUMENTATION?  
- ARE THERE ANY STATES OR LABELS THAT FEEL VAGUE, LIKE "MEDIUM" WITHOUT CONTEXT?

3) TRUST AND RISK  
- IF THIS BEHAVIOR IS WRONG OR FAILS SOMETIMES, HOW BAD IS IT FOR USER TRUST?  
- SHOULD I ASK THE USER TO CONFIRM INSTEAD OF DOING THIS SILENTLY?

4) REUSE VS NEW SURFACE  
- CAN I REUSE EXISTING COMPONENTS, APIS, OR STATE TO ACHIEVE THIS?  
- IF I ADD NEW STATE (FLAGS, STORAGE, TABLES), WHAT LONG‑TERM MAINTENANCE COST AM I CREATING?

5) PHASE‑AWARE QUALITY  
- GIVEN THE CURRENT PHASE, IS IT OK TO DEFER TESTS OR POLISHED ERROR MESSAGES, OR ARE WE CLOSE ENOUGH TO LAUNCH THAT THESE MUST BE INCLUDED?  
- DOES THIS CHANGE FIT MY CURRENT GOAL: PROOF, BUILD OUT, OR POLISH?

6) PERFORMANCE  
- WILL USERS NOTICE ANY SLOWNESS OR JANK FROM THE SIMPLEST IMPLEMENTATION?  
- IF I ADD CACHING OR OTHER COMPLEXITY, IS THE EXTRA MENTAL AND CODE COST WORTH THE SPEED GAIN?

7) SECURITY AND PRIVACY  
- COULD ANY LOG, ERROR, OR DATA STORE IN THIS CHANGE EXPOSE SECRETS OR PERSONAL INFORMATION?  
- AM I STAYING ON THE SAFE SIDE WHEN I AM NOT SURE?

8) LIBRARIES VS CUSTOM CODE  
- IS THERE A STABLE LIBRARY THAT MAKES THIS SAFER OR MORE RELIABLE THAN ROLLING MY OWN?  
- IF I ADD A LIBRARY, DOES IT SAVE ENOUGH COMPLEX, BUG‑PRONE CODE TO BE WORTH THE DEPENDENCY?
