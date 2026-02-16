# State Design Patterns

## Core Principle

State should be MINIMAL. If it can be derived, derive it.

## Patterns

### 1. Derive Instead of Store

```jsx
// BAD - Redundant state
const [items, setItems] = useState([]);
const [count, setCount] = useState(0);
// Keeping count in sync with items is error-prone

// GOOD - Derive count
const [items, setItems] = useState([]);
const count = items.length;
```

### 2. Store IDs, Not Objects

```jsx
// BAD - Object reference breaks on list update
const [selectedItem, setSelectedItem] = useState(null);

// GOOD - ID survives list updates
const [selectedId, setSelectedId] = useState(null);
const selectedItem = items.find((i) => i.id === selectedId);
```

### 3. Normalize Nested Data

```jsx
// BAD - Nested updates are painful
const [users, setUsers] = useState([
  { id: 1, posts: [{ id: 1, comments: [...] }] }
]);

// GOOD - Flat normalized structure
const [users, setUsers] = useState({ 1: { id: 1, postIds: [1] } });
const [posts, setPosts] = useState({ 1: { id: 1, commentIds: [...] } });
const [comments, setComments] = useState({ ... });
```

### 4. Group Related State

```jsx
// BAD - Multiple related states
const [x, setX] = useState(0);
const [y, setY] = useState(0);

// GOOD - Single object for related values
const [position, setPosition] = useState({ x: 0, y: 0 });
```

### 5. Avoid Contradictory State

```jsx
// BAD - Can have contradictory values
const [isLoading, setIsLoading] = useState(false);
const [error, setError] = useState(null);
const [data, setData] = useState(null);

// GOOD - Single status state
const [status, setStatus] = useState("idle"); // 'idle' | 'loading' | 'error' | 'success'
const [data, setData] = useState(null);
const [error, setError] = useState(null);

// BETTER - Use discriminated union or reducer
const [state, dispatch] = useReducer(reducer, { status: "idle" });
```

### 6. Lift State When Needed

```jsx
// If two components need same state, lift to nearest common ancestor

// Before: State in child, parent needs it
// After: State in parent, passed down as props

function Parent() {
  const [value, setValue] = useState("");
  return (
    <>
      <Input value={value} onChange={setValue} />
      <Preview value={value} />
    </>
  );
}
```

### 7. useState vs useReducer

Use `useReducer` when:

- State logic is complex
- Next state depends on previous state
- Multiple sub-values
- You want to test state logic in isolation

```jsx
const [state, dispatch] = useReducer(reducer, initialState);

function reducer(state, action) {
  switch (action.type) {
    case "increment":
      return { ...state, count: state.count + 1 };
    case "decrement":
      return { ...state, count: state.count - 1 };
    default:
      return state;
  }
}
```
