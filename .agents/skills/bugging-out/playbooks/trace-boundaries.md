# Trace the Boundaries

Fits when it breaks somewhere along a path, or only sometimes.

1. Write the path from input to symptom as a chain of handoffs: UI, handler, state, API, storage, library.
2. Log what goes in and out at a handoff in the middle. Reuse existing logs first.
3. Keep the half where right turns into wrong. Halve again.
4. If it turns wrong inside a dependency, read its source rather than guessing.
5. Intermittent: log event order with timestamps, add a delay to test a race, repeat 10-20 times.
6. Visual or speed: record and step frame by frame, measure, or profile.

Done when you can name the exact handoff where right turns into wrong.
