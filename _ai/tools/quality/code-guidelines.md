# 🏰 Code Quality Guidelines
_Prevention-Focused Development for Contract-First Feature Fortresses_

---

## 🎯 Purpose & Philosophy

This guide shifts from reactive code review to proactive code quality. Instead of catching issues after they're written, we prevent them during development by adopting defensive coding patterns and architectural discipline.

Core Philosophy: Write code that naturally resists common failure modes while maintaining velocity for solo indie development.

---

## 🏰 Mental Model: Contract-First Feature Fortress

Think of each vertical slice as a fortress with clear contracts governing all interactions:

### The Fortress Mindset
- Walls = Clear boundaries between features
- Gates = Well-defined interfaces with validation
- Guards = Error handling and input sanitization
- Keep = Core business logic protected inside
- Contracts = Explicit agreements about what goes in/out

### Contract-First Approach
1. Define the contract before writing implementation
2. Validate at boundaries - never trust external data
3. Fail fast and visibly when contracts are violated
4. Keep internals private - only expose what's necessary
5. Design for replaceability - any fortress should be swappable

---

## ⚖️ Core Principles

### 🎯 Single Responsibility per Fortress
Each vertical slice owns exactly one business capability and its complete stack (UI → Logic → Data).

### 🔒 Security by Default
Every boundary is a potential attack vector. Validate, sanitize, and authenticate at every gate.

### 🚀 Fail Fast, Fail Visible
Surface problems immediately with clear error messages rather than letting them cascade silently.

### 🧩 Composition over Configuration
Build with small, focused pieces that combine cleanly rather than large configurable components.

### 📊 Explicit over Implicit
Make dependencies, side effects, and data flows obvious in the code structure.

### ⚡ Performance Consciousness
Every operation has a cost. Consider the performance implications of architectural decisions.

---

## 🚧 Boundaries

### Defining Clean Boundaries

#### ✅ Good Boundary Patterns
```typescript
// Clear interface definition
interface UserService {
  authenticate(credentials: LoginCredentials): Promise<AuthResult>
  getCurrentUser(): Promise<User | null>
  logout(): Promise<void>
}

// Input validation at boundary
export async function authenticateUser(input: unknown): Promise<AuthResult> {
  const credentials = LoginCredentialsSchema.parse(input) // Validate first
  return userService.authenticate(credentials)
}
```

#### ❌ Boundary Violations
```typescript
// Direct database access across features
const user = await db.users.findFirst({ where: { id: userId } })

// Implicit dependencies
function calculateSavings() {
  const user = useUser() // Hidden dependency on auth context
  const purchases = usePurchases() // Hidden dependency on purchase context
}
```

### Boundary Enforcement Rules

1. No Direct Database Access - Always go through service layer
2. No Cross-Feature Imports - Use dependency injection or events
3. Validate All Inputs - Use runtime validation (Zod, io-ts)
4. Handle All Outputs - Wrap external calls in Result/Either types
5. Explicit Dependencies - Make all dependencies injectable/mockable

### Inter-Fortress Communication

#### Preferred: Events/Messages
```typescript
// Publisher doesn't know about subscribers
eventBus.emit('user.authenticated', { userId, timestamp })

// Subscriber handles its own concerns
eventBus.on('user.authenticated', (event) => {
  analytics.track('login', event)
})
```

#### Acceptable: Service Interfaces
```typescript
// Well-defined contract
interface NotificationService {
  sendWelcomeEmail(userId: string): Promise<Result<void, EmailError>>
}

// Dependency injection
class AuthService {
  constructor(private notifications: NotificationService) {}
}
```

#### Avoid: Direct Coupling
```typescript
// Tight coupling - auth knows about analytics
async function login(credentials) {
  const user = await authenticate(credentials)
  analytics.track('login', user) // ❌ Boundary violation
  return user
}
```

---

## 🧭 Prevention Heuristics

### 🧠 Functionality Heuristics
- Before writing logic: Define expected inputs, outputs, and edge cases
- Before async operations: Plan error scenarios and timeout handling
- Before state changes: Consider race conditions and rollback strategies

### 🧾 Readability Heuristics  
- Function naming: Should read like a sentence describing what it does
- Variable scope: Keep variables as close to usage as possible
- Magic numbers: Extract to named constants with explanatory comments

### 📐 Consistency Heuristics
- New patterns: Check if similar problems exist and reuse solutions
- Import styles: Follow existing import organization in the codebase
- Error handling: Use consistent Result/Either patterns across features

### ⚡ Performance Heuristics
- Before loops: Consider if operation can be batched or memoized
- Before API calls: Check if data can be cached or deduplicated
- Before re-renders: Verify dependencies are properly memoized

### 💡 Best Practices Heuristics
- Before copying code: Extract shared logic to utilities
- Before adding state: Consider if it can be derived or computed
- Before adding dependencies: Evaluate if lighter alternatives exist

### 🧪 Testing Heuristics
- Before implementation: Write test cases for expected behavior
- Complex logic: Ensure multiple input scenarios are covered
- External dependencies: Verify mocks match actual service contracts

### 🧯 Error Handling Heuristics
- At boundaries: Always validate and sanitize inputs
- Async operations: Handle network failures, timeouts, and partial failures
- User feedback: Provide actionable error messages, not technical details

---

## 🚨 Complexity Triggers

Stop and refactor when you encounter:

### Function-Level Triggers
- Lines: >30 lines in a single function
- Conditions: >5 conditional branches
- Nesting: >3 levels of indentation
- Parameters: >4 function parameters

### Component-Level Triggers
- Props: >8 props passed to a component
- State: >5 pieces of local state
- Effects: >3 useEffect hooks
- Renders: Conditional rendering >3 levels deep

### Architecture-Level Triggers
- Dependencies: Circular imports between features
- Coupling: Feature depends on >3 other features
- Duplication: Same logic in >2 places
- State: Global state modified by >3 features

### Action Required
When triggers are hit:
1. Pause implementation
2. Extract smaller functions/components
3. Introduce abstraction layers
4. Simplify data flow
5. Write tests before continuing

---

## 📐 Implementation Guidelines

### Starting a New Feature

1. Define the Contract
   ```typescript
   // Define types first
   interface FeatureState { }
   interface FeatureActions { }
   interface FeatureService { }
   ```

2. Create Boundaries
   ```typescript
   // Input validation
   const InputSchema = z.object({ })
   
   // Error types
   type FeatureError = 
     | ValidationError 
     | NetworkError 
     | BusinessLogicError
   ```

3. Build from Outside-In
   ```typescript
   // API layer first
   export const featureApi = { }
   
   // Service layer
   export const featureService = { }
   
   // Component layer last
   export const FeatureComponent = { }
   ```

### Modifying Existing Code

1. Understand Current Contracts
   - Read existing interfaces and types
   - Check how feature is currently used
   - Identify existing validation patterns

2. Maintain Backward Compatibility
   - Add new functionality alongside old
   - Deprecate gradually with clear migration paths
   - Version breaking changes explicitly

3. Test Contract Changes
   - Update types and see what breaks
   - Run integration tests across boundaries
   - Verify error scenarios still work

### Cross-Feature Integration

1. Use Event-Driven Architecture
   ```typescript
   // Publisher
   eventBus.emit('order.completed', orderData)
   
   // Subscriber
   eventBus.on('order.completed', handleOrderCompletion)
   ```

2. Dependency Injection
   ```typescript
   // Service interface
   interface PaymentService {
     processPayment(amount: Money): Promise<PaymentResult>
   }
   
   // Implementation injection
   const orderService = new OrderService(paymentService)
   ```

3. Shared Utilities Only
   ```typescript
   // ✅ Shared utility functions
   export const formatCurrency = (amount: number) => { }
   
   // ❌ Shared business logic
   export const calculateOrderTotal = (items: Item[]) => { }
   ```

---

## 🎯 Quality Checkpoints

Before committing code, verify:

### Contract Compliance
- [ ] All inputs validated with runtime checks
- [ ] All outputs properly typed and documented
- [ ] Error cases handled with specific error types
- [ ] No direct access to other feature internals

### Fortress Integrity
- [ ] Feature can be tested in isolation
- [ ] No hidden dependencies on global state
- [ ] External services properly mocked/stubbed
- [ ] Clear separation between UI, logic, and data layers

### Security Posture
- [ ] User inputs sanitized and validated
- [ ] Sensitive data not logged or exposed
- [ ] Authentication/authorization properly enforced
- [ ] No hardcoded secrets or configuration

### Performance Baseline
- [ ] No unnecessary re-renders or recomputations
- [ ] Expensive operations properly memoized
- [ ] Database queries optimized and bounded
- [ ] Bundle size impact considered

### Maintainability Standards
- [ ] Code reads like well-structured prose
- [ ] Business logic separate from framework code
- [ ] Configuration externalized and documented
- [ ] Deprecation path planned for breaking changes

### Testing Coverage
- [ ] Happy path scenarios covered
- [ ] Edge cases and error scenarios tested
- [ ] Integration points properly mocked
- [ ] Performance characteristics verified

---

## 🔄 Continuous Improvement

This guide evolves with the codebase. When you notice patterns that should be prevented:

1. Add to Prevention Heuristics - Turn reactive findings into proactive rules
2. Update Complexity Triggers - Adjust thresholds based on actual pain points  
3. Refine Boundaries - Improve interface patterns based on integration challenges
4. Enhance Checkpoints - Add verification steps for recurring issues

Remember: Prevention is cheaper than cure, especially for solo developers who wear all the hats.