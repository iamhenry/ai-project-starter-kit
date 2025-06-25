<tdd-refactor-phase>
Refactor Phase
   a. Code Quality Review (Reference: _ai/tools/quality/code-quality-guidelines.md):
      - ONLY apply fortress patterns when complexity triggers are hit (>30 lines, >5 conditions, >3 nesting)
      - Verify 🎯 QUALITY-CHECKED compliance for production-bound code only
      - Validate fortress integrity ONLY if feature crosses boundaries or has external dependencies
      - Ensure boundary enforcement ONLY at actual feature boundaries, not internal functions
      - Check security posture ONLY for user inputs and external data
      - Verify performance baseline ONLY for operations that impact user experience
   b. Pragmatic Improvements (Apply Minimally):
      - Extract duplicate code ONLY if >2 identical blocks exist
      - Create helper functions ONLY if logic is used >2 times
      - Refactor to fortress boundaries ONLY if mixing UI/logic/data in same function
      - Enhance readability ONLY if code is genuinely unclear
      - Apply prevention heuristics ONLY when natural refactoring opportunities exist
   c. Final Verification:
      - Run quality checkpoints from code-quality-guidelines.md ONLY for triggered complexity
      - Run tests to ensure refactoring didn't break anything
      - Document new shared components ONLY if they'll be reused
      - Stop refactoring when tests pass and code is readable
</tdd-refactor-phase>