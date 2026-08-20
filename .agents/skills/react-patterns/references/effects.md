# Effects Patterns

## When useEffect IS Needed

- Synchronizing with external systems (DOM APIs, third-party widgets)
- Data fetching (with proper cleanup)
- Setting up subscriptions
- Measuring DOM elements

## Anti-Patterns

### 1. Derived State in useEffect

```jsx
// BAD - Extra render cycle
const [fullName, setFullName] = useState("");
useEffect(() => {
  setFullName(firstName + " " + lastName);
}, [firstName, lastName]);

// GOOD - Calculate during render
const fullName = firstName + " " + lastName;
```

### 2. Caching with useEffect

```jsx
// BAD
useEffect(() => {
  setVisibleTodos(filterTodos(todos, filter));
}, [todos, filter]);

// GOOD - useMemo for expensive calculations
const visibleTodos = useMemo(() => filterTodos(todos, filter), [todos, filter]);
```

### 3. Reset State on Prop Change

```jsx
// BAD - Renders stale state first
useEffect(() => {
  setComment("");
}, [userId]);

// GOOD - Use key to reset entire component
<Profile userId={userId} key={userId} />;
```

### 4. Event Logic in useEffect

```jsx
// BAD - Fires on mount, not on action
useEffect(() => {
  if (product.isInCart) {
    showNotification("Added!");
  }
}, [product]);

// GOOD - In event handler
function handleBuyClick() {
  addToCart(product);
  showNotification("Added!");
}
```

### 5. Effect Chains

```jsx
// BAD - Cascading re-renders
useEffect(() => {
  setA(compute(x));
}, [x]);
useEffect(() => {
  setB(compute(a));
}, [a]);
useEffect(() => {
  setC(compute(b));
}, [b]);

// GOOD - Single calculation
function handleChange(x) {
  const a = compute(x);
  const b = compute(a);
  const c = compute(b);
  setFinalState({ a, b, c });
}
```

### 6. Notify Parent via useEffect

```jsx
// BAD - Extra render pass
useEffect(() => {
  onChange(isOn);
}, [isOn, onChange]);

// GOOD - Same event handler
function updateToggle(nextIsOn) {
  setIsOn(nextIsOn);
  onChange(nextIsOn); // Batched with state update
}
```

### 7. Store ID Instead of Object

```jsx
// BAD - Reset selection when items change
useEffect(() => {
  setSelection(null);
}, [items]);

// GOOD - Store ID, derive object
const [selectedId, setSelectedId] = useState(null);
const selection = items.find((item) => item.id === selectedId) ?? null;
```

## Proper Data Fetching

```jsx
// With cleanup for race conditions
useEffect(() => {
  let ignore = false;

  async function fetchData() {
    const result = await fetchResults(query);
    if (!ignore) {
      setResults(result);
    }
  }

  fetchData();
  return () => {
    ignore = true;
  };
}, [query]);
```

## External Store Subscription

```jsx
// BAD - Manual subscription
useEffect(() => {
  const unsub = store.subscribe(() => {
    setSnapshot(store.getState());
  });
  return unsub;
}, []);

// GOOD - Built-in hook
const snapshot = useSyncExternalStore(store.subscribe, store.getState);
```
