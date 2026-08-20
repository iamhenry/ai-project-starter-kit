# Event Handling Patterns

## Core Principle

Event logic belongs in event handlers, not Effects.

## 1. Named Handlers Over Inline

```jsx
// BAD - Logic hidden in JSX
<button
  onClick={() => {
    setLoading(true);
    api.save(data).then(() => {
      setLoading(false);
      showToast("Saved!");
    });
  }}
>
  Save
</button>;

// GOOD - Named, testable, readable
function handleSave() {
  setLoading(true);
  api.save(data).then(() => {
    setLoading(false);
    showToast("Saved!");
  });
}

<button onClick={handleSave}>Save</button>;
```

## 2. Event Handler Naming

```jsx
// Convention: handle + noun + verb
function handleFormSubmit() {}
function handleInputChange() {}
function handleButtonClick() {}
function handleUserDelete() {}

// For props: on + noun + verb
<Form onFormSubmit={handleFormSubmit} />
<Input onValueChange={handleInputChange} />
```

## 3. Batch Related Updates

```jsx
// React 18+ batches these automatically
function handleClick() {
  setCount((c) => c + 1); // Batched
  setFlag((f) => !f); // Batched
  // Single re-render
}

// For related state, update together
function handleSubmit() {
  setStatus("submitting");
  api.submit(data).then(
    () => {
      setStatus("success");
      setData(null); // Related updates together
    },
    () => setStatus("error"),
  );
}
```

## 4. Pass Events Up Properly

```jsx
// Child notifies parent in same handler
function Toggle({ isOn, onChange }) {
  function handleToggle() {
    const nextValue = !isOn;
    onChange(nextValue); // Notify parent immediately
  }

  return <button onClick={handleToggle}>{isOn ? "ON" : "OFF"}</button>;
}

// NOT via useEffect (causes extra render)
// BAD
useEffect(() => {
  onChange(isOn);
}, [isOn, onChange]);
```

## 5. Prevent Default and Stop Propagation

```jsx
function handleSubmit(e) {
  e.preventDefault(); // Prevent form submission
  // Custom handling
}

function handleClick(e) {
  e.stopPropagation(); // Prevent bubbling to parent
  // Handle only this element
}
```

## 6. Async Event Handlers

```jsx
// Handle async properly
async function handleSave() {
  try {
    setStatus("saving");
    await api.save(data);
    setStatus("saved");
  } catch (error) {
    setStatus("error");
    setError(error.message);
  }
}

// Or with .then()
function handleSave() {
  setStatus("saving");
  api
    .save(data)
    .then(() => setStatus("saved"))
    .catch((err) => {
      setStatus("error");
      setError(err.message);
    });
}
```

## 7. Debouncing Events

```jsx
// For rapid-fire events (typing, scrolling)
function SearchInput() {
  const [query, setQuery] = useState("");

  // Debounce the API call, not the input
  const debouncedQuery = useDebounce(query, 300);

  useEffect(() => {
    if (debouncedQuery) {
      searchApi(debouncedQuery);
    }
  }, [debouncedQuery]);

  // Input updates immediately for responsiveness
  return <input value={query} onChange={(e) => setQuery(e.target.value)} />;
}
```

## 8. Event Delegation

```jsx
// For many similar elements, delegate to parent
function List({ items, onItemClick }) {
  function handleClick(e) {
    const itemId = e.target.dataset.id;
    if (itemId) {
      onItemClick(itemId);
    }
  }

  return (
    <ul onClick={handleClick}>
      {items.map((item) => (
        <li key={item.id} data-id={item.id}>
          {item.name}
        </li>
      ))}
    </ul>
  );
}
```
