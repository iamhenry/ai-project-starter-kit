# Performance Patterns

## Core Rule

MEASURE FIRST. Premature optimization wastes time and adds complexity.

## When to Optimize

1. User-visible lag (>100ms interactions)
2. Profiler shows component re-rendering excessively
3. Expensive calculations running on every render

## useMemo - Expensive Calculations

```jsx
// WHEN TO USE: Calculation takes >1ms
const sortedItems = useMemo(
  () => items.sort((a, b) => a.name.localeCompare(b.name)),
  [items],
);

// WHEN NOT TO USE: Simple operations
// BAD - Adds overhead for trivial computation
const doubled = useMemo(() => count * 2, [count]);

// GOOD - Just compute it
const doubled = count * 2;
```

## useCallback - Stable Function References

```jsx
// WHEN TO USE: Function passed to memoized child
const MemoizedChild = memo(function Child({ onClick }) {
  return <button onClick={onClick}>Click</button>;
});

function Parent() {
  // Needed because MemoizedChild uses memo()
  const handleClick = useCallback(() => {
    doSomething();
  }, []);

  return <MemoizedChild onClick={handleClick} />;
}

// WHEN NOT TO USE: Function not passed to memoized component
// BAD - Unnecessary overhead
const handleClick = useCallback(() => setCount((c) => c + 1), []);
return <button onClick={handleClick}>+</button>;

// GOOD - Just define the function
return <button onClick={() => setCount((c) => c + 1)}>+</button>;
```

## memo - Skip Re-renders

```jsx
// WHEN TO USE: Component renders same output for same props
const ExpensiveList = memo(function ExpensiveList({ items }) {
  return items.map((item) => <ExpensiveItem key={item.id} item={item} />);
});

// WHEN NOT TO USE: Props change on every render anyway
// BAD - Props always change, memo does nothing
const Item = memo(function Item({ data }) {
  return <div>{data.name}</div>;
});

// Parent creates new object every render
<Item data={{ name: "test" }} />; // memo is useless here
```

## List Virtualization

```jsx
// For long lists (100+ items), render only visible items
import { useVirtualizer } from "@tanstack/react-virtual";

function VirtualList({ items }) {
  const parentRef = useRef(null);
  const virtualizer = useVirtualizer({
    count: items.length,
    getScrollElement: () => parentRef.current,
    estimateSize: () => 50,
  });

  return (
    <div ref={parentRef} style={{ height: 400, overflow: "auto" }}>
      <div style={{ height: virtualizer.getTotalSize() }}>
        {virtualizer.getVirtualItems().map((virtualItem) => (
          <div
            key={virtualItem.key}
            style={{
              position: "absolute",
              top: virtualItem.start,
              height: virtualItem.size,
            }}
          >
            {items[virtualItem.index].name}
          </div>
        ))}
      </div>
    </div>
  );
}
```

## Code Splitting

```jsx
// Lazy load heavy components
const HeavyChart = lazy(() => import("./HeavyChart"));

function Dashboard() {
  return (
    <Suspense fallback={<ChartSkeleton />}>
      <HeavyChart />
    </Suspense>
  );
}
```

## Avoid These Performance Killers

```jsx
// 1. Object/array literals in JSX (new reference every render)
// BAD
<Child style={{ color: 'red' }} items={[1, 2, 3]} />

// GOOD - Define outside or useMemo
const style = { color: 'red' };
const items = [1, 2, 3];
<Child style={style} items={items} />

// 2. Inline function in dependency array
// BAD - Effect runs every render
useEffect(() => {
  fetchData();
}, [() => fetchData]); // New function every time!

// 3. Spreading props unnecessarily
// BAD - Passes everything, hard to track
<Child {...props} />

// GOOD - Be explicit
<Child name={props.name} id={props.id} />
```
