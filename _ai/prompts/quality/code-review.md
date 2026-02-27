<code-review>
# 🧠 Hybrid Code Review  
_A two-phase approach to balance precision and breadth_

---

## Pre-steps
1. Dont write any code.
2. run `git status` command to get the recent code changes
3. If there are no uncommitted changes, review the codebase state.
4. Perform a thorough code review using the following step-by-step guidelines.
5. Prefix each review with an emoji indicating a rating.
6. Score: Rate the code quality on a scale of 1-10, with 10 being best.
7. Provide Brief Summary and Recommendations.

---

## PHASE 1 — 🎯 Focused Local Review (Always Perform)

Review only the modified files and directly affected logic.

- [ ] 🧠 Functionality — Does the change fulfill its purpose and handle edge cases?
- [ ] 🧾 Readability — Clear variable, function, and file naming? Easy to follow?
- [ ] 📐 Consistency — Coding style and architectural conventions followed?
- [ ] ⚡️ Performance — Any potential slowdowns or unoptimized operations?
- [ ] 💡 Best Practices — DRY, modular, SOLID, minimal duplication?
- [ ] ✂️ KISS — Is this the simplest solution that solves the current need?
- [ ] 🚫 YAGNI — Does this avoid speculative features/abstractions not needed now?
- [ ] 🧪 Test Coverage — Are there adequate, meaningful tests? All tests passing?
- [ ] 🧯 Error Handling — Are errors handled gracefully without leaking info?

---

## SYSTEM REVIEW TRIGGER — 🕵️ Check If System-Wide Analysis Is Needed

Trigger Phase 2 if any of these are true:

- [ ] Affects shared modules, global state, or commonly reused logic  
- [ ] Changes public interfaces, exported APIs, or shared components  
- [ ] Introduces or modifies asynchronous logic or side effects  
- [ ] Appears to impact state across features or modules  
- [ ] Raises security, performance, or architectural concerns  

---

## PHASE 2 — 🔁 System-Wide Review (Only If Triggered)

> ⚠️ Only assess each section below if it’s relevant to the code being changed.

- [ ] 🔒 Security  
    - Input sanitization?  
    - Data leakage, XSS, SQL injection, token misuse?

- [ ] 🧵 Race Conditions  
    - Async safety?  
    - Parallel writes, shared state mutations?

- [ ] 🧠 Memory Leaks  
    - Cleanup of listeners, intervals, subscriptions, retained DOM references?

- [ ] 🎞️ Animation Leaks  
    - UI transitions detached on unmount?  
    - Avoiding infinite or wasteful repaints?

- [ ] 🔄 State Management  
    - Predictable, well-scoped, normalized state logic?  
    - Avoids unnecessary re-renders or duplication?

- [ ] 📊 Observability  
    - Logs meaningful and contextual?  
    - Monitoring/tracing in place for critical flows?

- [ ] 🧬 Schema/Type Validation  
    - Validates inputs/outputs with Zod, io-ts, or runtime guards?  
    - Are types used effectively at compile-time (e.g., TypeScript)?

- [ ] 🏛️ Architecture  
    - Violates layering or introduces tight coupling?  
    - Shared responsibilities without separation of concerns?

---

## 🧱 Code Smells Checklist (Always Worth Surfacing)

- [ ] 🔁 Duplicated Code — Can logic be abstracted or reused?
- [ ] 🧬 Long Methods — Can complex logic be split into smaller functions?
- [ ] 🧩 Large/God Classes — Too many responsibilities in one place?
- [ ] 🧗 Deep Nesting — Favor guard clauses or early returns to flatten logic
- [ ] 🔗 Tight Coupling — Is this module overly dependent on others?
- [ ] 💔 Low Cohesion — Unrelated behaviors grouped together?
- [ ] 🪙 Primitive Obsession — Using raw types where objects/enums make sense?

---

## 🗂️ Issue Output Format

For each issue identified:

- File: `path/to/file.ts:42–45` or `path/to/file.ts:42`
- Severity: High / Medium / Low / `[THEORETICAL]`
- Perspective: Phase 1 / Phase 2 / Both
- Evidence: Quote the specific line(s) that prove the problem exists
- Issue: Brief description of the problem
- Why This Severity: Explain impact or potential harm
- Suggestion: Recommend a specific fix or approach
- Include the relevant lines of code illustrating the issue.
- Code Snippet Example (adapt to other languages if when necessary) 
```typescript
// File: utils/formatter.ts:42-45
export function formatDate(date: Date) {
  return date.toISOString().split('T')[0];
// Missing timezone offset handling
}
```

---

## 🧮 Severity Guidelines

Before assigning severity, apply this test:
> **"Can I point to a specific line of code that demonstrates this problem?"**
> - YES → assign based on impact below
> - NO → it's speculation; downgrade one level or flag as `[THEORETICAL]`

- HIGH — Must fix before release: crashes, regressions, data loss, security flaws, memory/race bugs  
  _Requires: direct evidence in the diff, not a chain of "could" statements_
- MEDIUM — Should fix soon: architectural drift, test gaps, performance concerns  
  _Requires: observable pattern in the code, not just a possible future state_
- LOW — Optional fix: style, naming, minor smells, doc improvements  
  _Theoretical risks belong here by default unless evidence elevates them_

---

## ✅ Triangulated Review Summary

- [ ] Emoji-prefixed scores for each applicable section
- [ ] Convergence: issues found by both Phase 1 and Phase 2
- [ ] Divergence: Phase 1-only and Phase 2-only findings
- [ ] Overall quality rating: `1–10`
- [ ] Blockers listed with severity
- [ ] Summary of feedback and top action items

---

## 🎯 Next Steps Decision Framework

After completing the code review, use this framework to determine the appropriate next actions:

### 🚦 Action Decision Matrix

**Based on Overall Rating:**
- **9-10/10**: ✅ **Ready to Merge** - Optional minor improvements only
- **7-8/10**: ⚠️ **Address Medium Issues** - Fix before merge, low issues optional  
- **5-6/10**: 🔄 **Requires Rework** - Address high and medium issues, consider architectural changes
- **1-4/10**: 🛑 **Major Revision Needed** - Significant rework required before re-review

### 📋 Action Categories

#### 🔥 IMMEDIATE (Before Merge)
_Must address before code can be merged_

- [ ] **HIGH Severity Issues** - All high severity issues must be resolved
- [ ] **Breaking Changes** - Any changes that break existing functionality
- [ ] **Security Vulnerabilities** - Security-related issues require immediate attention
- [ ] **Test Failures** - All tests must pass
- [ ] **Memory/Race Conditions** - Critical system stability issues

#### ⏰ NEXT SPRINT (Within 1-2 Sprints)
_Should be addressed soon to prevent technical debt_

- [ ] **MEDIUM Severity Issues** - Architectural concerns and performance issues
- [ ] **Test Coverage Gaps** - Missing test coverage for critical functionality
- [ ] **Documentation Updates** - Code comments and documentation improvements
- [ ] **Consistency Issues** - Architectural or style inconsistencies

#### 🔮 FUTURE BACKLOG (Nice to Have)
_Improvements that can be scheduled for later_

- [ ] **LOW Severity Issues** - Style, naming, minor code smells
- [ ] **Optimization Opportunities** - Performance improvements without urgent need
- [ ] **Code Refactoring** - Non-critical structural improvements
- [ ] **Enhancement Ideas** - Suggestions for feature improvements

### 🛠️ Implementation Actions

#### For Code Author:
1. **Address Immediate Issues** - Fix all high severity and blocking issues
2. **Update Tests** - Ensure test coverage for any new functionality
3. **Update Documentation** - Revise comments and docs as needed
4. **Request Re-review** - If significant changes were made

#### For Reviewer:
1. **Verify Fixes** - Confirm that immediate issues have been resolved
2. **Approve or Request Changes** - Based on remaining issue severity
3. **Create Follow-up Tickets** - For next sprint and backlog items
4. **Update Team Knowledge** - Share insights or patterns discovered

### 📊 Follow-up Template

```markdown
## 🎯 Review Follow-up Actions

### ✅ Immediate Actions (Required before merge):
- [ ] Fix security vulnerability in auth.ts:42
- [ ] Add error handling for async operations
- [ ] Resolve failing test in user-service.test.ts

### ⏰ Next Sprint Actions:
- [ ] JIRA-123: Improve test coverage for payment flow
- [ ] JIRA-124: Refactor user state management for consistency
- [ ] JIRA-125: Add performance monitoring to critical paths

### 🔮 Future Backlog:
- [ ] Consider extracting shared utilities to reduce duplication
- [ ] Explore alternative state management patterns
- [ ] Add comprehensive error logging throughout app

### 📝 Notes:
- Author estimated 2-3 hours for immediate fixes
- Medium issues align with existing technical debt initiatives
- Consider scheduling architecture review session for consistency issues
```

---

## Output Example
```markdown
## 📊 Overall Rating: 8.5/10 🟢

### Triangulated Summary
The implementation successfully addresses screen dismissal and email verification feedback issues by introducing a robust toast notification system and improving authentication flow UX. The code demonstrates solid architecture with proper error handling, animation, and lifecycle management.

### 🔗 Convergence (Both Perspectives)
- Hardcoded timeout introduces reliability risk in async UI flow

### 🔀 Divergence (Unique Findings)
- Phase 1 only: Toast color mapping maintainability concern
- Phase 2 only: Toast container placement has app-wide consistency impact

### 🎯 Recommended Next Steps: ⚠️ Address Medium Issues
_Rating: 8.5/10 - Fix 2 medium severity issues before merge, low severity optional_

---

## 🔍 Detailed Review by Category

#### 1. 🎯 Functionality - Score: 8/10 ✅
✅ Strengths:
- Successfully addresses the core issue: signup modal not dismissing and lack of email verification feedback
- Proper conditional behavior: only dismiss modal on success, stay on screen for errors  
- Toast implementation provides clear user feedback for email verification  
- Router navigation correctly integrated with existing auth flow  

⚠️ Areas for Improvement:
- File: `app/(app)/sign-up.tsx:69-71` 
- Severity: Medium
- Perspective: Both
- Issue: Hardcoded 300ms timeout for toast display  
- Why This Severity: Could create race conditions or timing issues on slower devices  
- Suggestion: Use navigation state listener or Promise.resolve().then() for more reliable timing
- Code Snippet:
    ~~~typescript
    // File: app/(app)/sign-up.tsx:69-71
    setTimeout(() => {
      showToast('Please check your email to verify your account', 'info');
      router.dismissAll();
    }, 300); // Hardcoded timeout - potential race condition
    ~~~

---

#### 2. 📖 Readability - Score: 8/10 ✅
✅ Strengths:
- Clear, descriptive comments explaining modal dismissal behavior  
- Consistent import organization and naming conventions  
- Well-structured toast provider with clear interface  
- Good separation of concerns in toast component and context  

⚠️ Areas for Improvement:
- File: `components/ui/toast.tsx:52-60`
- Severity: Low
- Perspective: Phase 1
- Issue: Switch statement could benefit from a color mapping object  
- Why This Severity: Minor maintainability improvement, doesn't affect functionality  
- Suggestion: Extract color mapping to constants for easier maintenance
- Code Snippet:
    ~~~typescript
    // File: components/ui/toast.tsx:52-60
    switch (type) {
      case 'success': return 'bg-green-500';
      case 'error': return 'bg-red-500';
      case 'info': return 'bg-blue-500';
      default: return 'bg-gray-500';
    } // Consider extracting to TOAST_COLORS constant
    ~~~

---

#### 3. 🔄 Consistency - Score: 6/10 🟡
⚠️ Issues Identified:

- File: `app/(app)/sign-in.tsx:45` 
- Severity: Medium
- Perspective: Phase 2
- Issue: Sign-in doesn't provide user feedback like sign-up does  
- Why This Severity: Inconsistent user experience between auth flows  
- Suggestion: Add toast notification for successful sign-in or error feedback

- File: `app/(app)/welcome.tsx:16`
- Severity: Medium
- Perspective: Phase 2
- Issue: ToastContainer only added to welcome screen, not consistently across app  
- Why This Severity: Limits toast functionality to single screen, breaks expected behavior  
- Suggestion: Consider adding ToastContainer to main layout or implement global toast positioning
- Code Snippet:
    ~~~typescript
    // File: app/(app)/welcome.tsx:16
    <ToastContainer /> {/* Only on welcome screen - should be global */}
    ~~~

---

### 🎯 Follow-up Actions Required

#### ✅ Immediate Actions (Before merge):
- [ ] None - no high severity issues identified

#### ⏰ Next Sprint Actions:
- [ ] Fix hardcoded timeout in sign-up.tsx (Medium severity)
- [ ] Add consistent toast feedback to sign-in flow (Medium severity)  
- [ ] Move ToastContainer to global layout (Medium severity)

#### 🔮 Future Backlog:
- [ ] Refactor toast color mapping to constants (Low severity)
- [ ] Consider comprehensive toast notification strategy across app

### 📝 Review Notes:
- Strong implementation overall with good architecture
- Focus on consistency improvements to enhance user experience
- No blocking issues, safe to merge after addressing medium severity items
```
</code-review>
