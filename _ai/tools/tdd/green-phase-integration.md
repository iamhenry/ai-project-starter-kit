<green-phase-integration>
# 🟢 Integration Test Green Phase Prompt (BDD Driven)

## Objective
Implement the minimal functionality necessary to make BDD scenario tests pass. Focus on delivering complete user experiences that match business requirements.

## Required Context Files
- Failing integration tests from Red Phase
- BDD scenarios with acceptance criteria and edge cases
- Existing system architecture (entry points, data flow, system boundaries)
- Feature interfaces that need implementation
- Persistence contracts that need implementation
- State management patterns used in the system

## Process

### 1. Analyze Failing Tests
- Run test command for the test file to analyze and understand why it's failing.
- Search codebase to gather relevant files to help you pass these tests.
- Identify broken user journey: Which user experience is incomplete?
- Determine missing functionality: What prevents user success?
- Map to system architecture: Which layers/modules need implementation?
- Prioritize by user impact: Focus on core user value first

### 2. Implementation Priority (User-First)
1. User interaction layer: Entry points, interfaces, user touchpoints
2. Critical state management: Data that drives user experience
3. Data persistence: State that must survive system sessions
4. Business rules enforcement: Requirements from acceptance criteria
5. System integration points: Where modules connect to complete flows
6. Error handling: Graceful failures that don't break user experience

### 3. Implementation Strategy (Minimal Viable User Experience)
```
// Follow the user path through your system
// 1. Entry point (where users start)
// 2. State management (what drives user experience)
// 3. Persistence layer (what survives sessions)
// 4. Module integration (connecting system pieces)
// 5. Business logic (enforcing requirements)
```

### 4. Implementation Guidelines
- Follow the user path: Implement in the order users experience it
- Implement complete flows: Don't leave partial user journeys
- Handle state persistence: Critical for user experience continuity
- Enforce business rules: Requirements from acceptance criteria
- Keep it simple: Minimal code to satisfy user requirements
- Test frequently: Run integration tests after each implementation step

### 5. Verification Approach
- Run integration tests: After each implementation step
- Verify complete user journey: User can finish the entire flow
- Test state persistence: Critical data survives system restarts
- Validate business rules: Requirements are properly enforced
- Check edge cases: Handle scenarios from BDD edge cases
- Manual verification: Actually use the feature as intended

### 6. Implementation Checklist (Per BDD Scenario)
- [ ] User can initiate the journey (entry point works)
- [ ] User can progress through the flow (transitions work)
- [ ] User can complete the journey (success state reached)
- [ ] Critical state persists across system sessions
- [ ] Business rules are enforced
- [ ] Error cases are handled gracefully
- [ ] Integration test passes
- [ ] Manual user verification confirms experience

### 7. Code Quality Guidelines
- KISS: Keep implementation simple and focused on user value
- DRY: Extract reusable patterns, but don't over-engineer
- YAGNI: Only implement what's needed for current user scenarios
- Single Responsibility: Each module has a clear user-facing purpose
- Testable: Code supports the integration tests you've written

## Success Criteria
- ✅ All BDD scenario integration tests pass
- ✅ Users can complete journeys described in scenarios
- ✅ Critical user state persists across system sessions
- ✅ Business rules from acceptance criteria are enforced
- ✅ User experience is smooth and intuitive
- ✅ Edge cases from BDD scenarios are handled
- ✅ No technical debt that impacts user experience
- ✅ Manual testing confirms the feature works as intended

## Common Implementation Mistakes to Avoid
- ❌ Implementing technical features that don't serve user needs
- ❌ Over-engineering solutions beyond BDD requirements
- ❌ Ignoring state persistence requirements
- ❌ Implementing partial user flows
- ❌ Focusing on making tests pass without considering user experience
- ❌ Adding complexity that doesn't match BDD scenarios
- ❌ Skipping manual verification of user experience

## Post-Implementation Verification
1. Integration tests pass: All BDD scenarios work
2. Manual user testing: Actually use the feature
3. State persistence testing: Restart system, verify state
4. Business rule validation: Requirements are enforced
5. Edge case verification: Handle error scenarios gracefully
6. User experience review: Flow feels natural and intuitive


<essential-debugging-commands>
### Capture All Errors (Setup Failures)
```bash
[TEST_RUNNER] [TEST_FILE] 2>&1 | head -50
```
When: First debugging attempt, missing database/mock errors

### Focus on Single Failing Test
```bash
[TEST_RUNNER] --filter="[SCENARIO_NAME]" --verbose
```
When: One specific BDD scenario keeps failing

### Watch Mode (Rapid Iteration)
```bash
[TEST_RUNNER] [TEST_FILE] --watch
```
When: Implementing integration logic, need instant feedback

### Debug Hanging Tests
```bash
[TEST_RUNNER] --detectOpenHandles --runInBand [TEST_FILE]
```
When: Tests never complete, suspect async issues

### Single-Threaded Execution
```bash
[TEST_RUNNER] --runInBand [TEST_FILE]
```
When: Race conditions, flaky test failures

### Environment Debug Mode
```bash
DEBUG=true LOG_LEVEL=debug [TEST_RUNNER] [TEST_FILE]
```
When: Configuration issues, environment setup problems
</essential-debugging-commands>
</green-phase-integration>