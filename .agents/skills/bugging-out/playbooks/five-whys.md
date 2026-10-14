# Five Whys

Use when the failing spot is known but the fix would only treat the symptom.

Follow the `five-whys` skill (`.agents/skills/5-whys/SKILL.md`). In short:

1. Ask one why. Gather evidence. Answer it with a file, line, or log.
2. Ask the next why only if it narrows the cause. Five is a reminder, not a quota.
3. Stop at the deepest cause you can fix within scope. Name anything deeper that is out of scope.

Done when the fix targets a cause, not a symptom, and every step cites evidence.
