# Component Patterns

## 1. Composition Over Configuration

```jsx
// BAD - Configuration prop explosion
<Card
  title="Hello"
  titleSize="lg"
  showIcon
  iconPosition="left"
  footer={<Button>Save</Button>}
/>

// GOOD - Composition
<Card>
  <Card.Header>
    <Icon />
    <Card.Title size="lg">Hello</Card.Title>
  </Card.Header>
  <Card.Footer>
    <Button>Save</Button>
  </Card.Footer>
</Card>
```

## 2. Controlled vs Uncontrolled

```jsx
// UNCONTROLLED - Component owns state
function UncontrolledInput() {
  const [value, setValue] = useState("");
  return <input value={value} onChange={(e) => setValue(e.target.value)} />;
}

// CONTROLLED - Parent owns state
function ControlledInput({ value, onChange }) {
  return <input value={value} onChange={(e) => onChange(e.target.value)} />;
}

// HYBRID - Default to uncontrolled, allow controlled
function Input({ value: controlledValue, onChange, defaultValue = "" }) {
  const [internalValue, setInternalValue] = useState(defaultValue);
  const isControlled = controlledValue !== undefined;
  const value = isControlled ? controlledValue : internalValue;

  const handleChange = (e) => {
    if (!isControlled) setInternalValue(e.target.value);
    onChange?.(e.target.value);
  };

  return <input value={value} onChange={handleChange} />;
}
```

## 3. Use Keys for Identity

```jsx
// Reset component state when user changes
<UserProfile userId={userId} key={userId} />

// Force re-mount on route change
<Editor key={documentId} />
```

## 4. Render Props Pattern

```jsx
// When children need parent's internal state
function Mouse({ render }) {
  const [position, setPosition] = useState({ x: 0, y: 0 });
  // ... track mouse
  return render(position);
}

// Usage
<Mouse render={({ x, y }) => <Cursor x={x} y={y} />} />;
```

## 5. Custom Hooks for Logic Reuse

```jsx
// Extract reusable logic into hooks
function useDebounce(value, delay) {
  const [debouncedValue, setDebouncedValue] = useState(value);

  useEffect(() => {
    const timer = setTimeout(() => setDebouncedValue(value), delay);
    return () => clearTimeout(timer);
  }, [value, delay]);

  return debouncedValue;
}

// Usage
const debouncedSearch = useDebounce(searchTerm, 300);
```

## 6. Avoid Prop Drilling

```jsx
// BAD - Passing through many layers
<App user={user}>
  <Layout user={user}>
    <Sidebar user={user}>
      <UserMenu user={user} />
    </Sidebar>
  </Layout>
</App>

// OPTION 1: Component composition
<App>
  <Layout sidebar={<Sidebar><UserMenu user={user} /></Sidebar>}>
    {children}
  </Layout>
</App>

// OPTION 2: Context for truly global data
const UserContext = createContext(null);

function App() {
  return (
    <UserContext.Provider value={user}>
      <Layout />
    </UserContext.Provider>
  );
}

function UserMenu() {
  const user = useContext(UserContext);
  // ...
}
```

## 7. Error Boundaries

```jsx
class ErrorBoundary extends React.Component {
  state = { hasError: false };

  static getDerivedStateFromError(error) {
    return { hasError: true };
  }

  render() {
    if (this.state.hasError) {
      return this.props.fallback;
    }
    return this.props.children;
  }
}

// Usage - Wrap risky components
<ErrorBoundary fallback={<ErrorMessage />}>
  <RiskyComponent />
</ErrorBoundary>;
```
