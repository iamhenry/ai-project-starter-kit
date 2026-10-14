# Trace the Boundaries

Use when the bug happens somewhere between layers, or only sometimes.

1. Write the path from input to symptom as a chain of handoffs: UI, handler, state, API, storage, library.
2. At each handoff, log what goes in and what comes out. Reuse existing logs first.
3. Find the first handoff where the value is wrong. Split that segment in half and repeat.
4. If the wrong value starts inside a dependency, read its source. Do not guess its behavior.
5. Timing bugs: log event order with timestamps, add a deliberate delay to test a race, run it 10-20 times.
6. Visual or speed bugs: record and step frame by frame, measure positions, profile. Do not eyeball.

Done when you can name the exact handoff where right turns into wrong.
