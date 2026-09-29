# Figma API recipes

Read the main skill first for tab attachment, execution, capture, and cleanup. Each recipe runs inside `page.evaluate` unless its code explicitly uses runner globals. Replace example IDs and labels with values observed in the intended editor. Creation dimensions are examples, not an inferred user requirement.

## Guard every write

Keep the attached editor URL, observed page ID, and target node ID in the task context. Use the URL when attaching and page/node checks when writing. If `f.fileKey` was available during inspection, compare it too. Do not invent a file key or bypass a changed-page guard.

```js
const result = await page.evaluate(async input => {
  const f = window.figma;
  if (!f?.currentPage || f.currentPage.id !== input.pageId) {
    throw new Error("Target page changed; inspect before writing");
  }
  const node = await f.getNodeByIdAsync(input.nodeId);
  if (!node || node.type !== input.type || node.name !== input.originalName) {
    throw new Error("Target node changed; inspect before writing");
  }
  if (node.parent?.id !== f.currentPage.id &&
      !f.currentPage.findOne(n => n.id === node.id)) {
    throw new Error("Target node is outside the expected page");
  }
  node.name = input.newName;
  return { id: node.id, name: node.name, type: node.type };
}, {
  pageId: "<observed page ID>", nodeId: "<observed node ID>",
  type: "RECTANGLE", originalName: "<observed name>", newName: "<requested name>"
});
return result;
```

This renames a layer, not the Figma file. Do not perform a temporary rename smoke test unless requested. For a reversible smoke, record the original name and restore the same node only if its name still equals the temporary value. Never restore over someone else's intervening edit.

Inspect a small relevant subtree, not the whole document. A frame's `children` and `findAll` provide descendants. Return only requested text, geometry, styles, and IDs. Confirm selection length before treating the current selection as one source. IDs in API calls contain colons; URL `node-id` values often contain hyphens. Prefer the ID returned by the API.

## Fonts and existing text

List available fonts once and load the exact family/style before setting `fontName`, `characters`, or text properties that require loaded fonts. Do not assume SF Pro or emoji fonts are available. Inter was available in the proven workflow, but must still be checked in the current editor.

```js
const fonts = await page.evaluate(async () => {
  const available = await window.figma.listAvailableFontsAsync();
  return available.map(entry => entry.fontName);
});
return fonts;
```

For a guarded existing TEXT node `textNode` and API object `f`:

```js
if (textNode.type !== "TEXT") throw new Error("Expected editable text");
const used = textNode.fontName === f.mixed
  ? textNode.getRangeAllFontNames(0, textNode.characters.length)
  : [textNode.fontName];
for (const font of used) await f.loadFontAsync(font);
textNode.characters = requestedText;
```

The fragment above needs `textNode` and `requestedText` from the guarded write. For an empty mixed-font node, choose and load an available font first. Replacing rich text can change its range styling. Preserve or explicitly reapply required styles; report a substitution rather than silently changing typography. Assign fresh arrays for fills, strokes, and effects rather than mutating a returned paint object in place.

## Build a native UI frame

This complete example creates one native frame beside a top-level source on the current page. It includes editable text, a rounded card, and a native shape button. Use it as a starting point for the requested design, not as a substitute for reading the source image. Match the target dimensions and content to the user's ask.

```js
const result = await page.evaluate(async input => {
  const f = window.figma;
  if (!f?.currentPage || f.currentPage.id !== input.pageId) {
    throw new Error("Target page changed");
  }
  const source = await f.getNodeByIdAsync(input.sourceId);
  if (!source || source.parent?.id !== f.currentPage.id) {
    throw new Error("Expected a top-level source on the current page");
  }
  if (f.currentPage.children.some(n => n.name === input.outputName)) {
    throw new Error("Output already exists; inspect it instead of duplicating");
  }
  const available = await f.listAvailableFontsAsync();
  for (const style of ["Regular", "Bold"]) {
    const font = { family: "Inter", style };
    if (!available.some(e => e.fontName.family === font.family &&
                            e.fontName.style === font.style)) {
      throw new Error("Required Inter font unavailable; choose an approved substitute");
    }
    await f.loadFontAsync(font);
  }
  const solid = (r, g, b) => [{ type: "SOLID", color: { r, g, b } }];
  const root = f.createFrame();
  try {
    root.name = input.outputName;
    root.resize(input.width, input.height);
    root.x = source.x + source.width + 100;
    root.y = source.y;
    root.fills = solid(1, 1, 1);
    root.clipsContent = true;
    root.visible = false;

    function rectangle(parent, name, x, y, w, h, paints, radius = 0) {
      const n = f.createRectangle();
      parent.appendChild(n);
      n.name = name; n.resize(w, h); n.x = x; n.y = y;
      n.fills = paints; n.cornerRadius = radius;
      return n;
    }
    function text(parent, name, content, x, y, width, size, style = "Regular") {
      const n = f.createText();
      parent.appendChild(n);
      n.name = name;
      n.fontName = { family: "Inter", style };
      n.fontSize = size;
      n.characters = content;
      n.fills = solid(0.07, 0.07, 0.07);
      n.resize(width, size * 1.4);
      n.textAutoResize = "HEIGHT";
      n.lineHeight = { unit: "PIXELS", value: size * 1.4 };
      n.x = x; n.y = y;
      return n;
    }
    const section = f.createFrame();
    root.appendChild(section);
    section.name = "Content"; section.resize(input.width - 48, 220);
    section.x = 24; section.y = 24; section.fills = [];
    section.clipsContent = false;
    text(section, "Title", "Weekly journal", 0, 0, section.width, 26, "Bold");
    rectangle(section, "Card background", 0, 60, section.width, 120,
              solid(0.98, 0.96, 0.91), 16);
    text(section, "Card copy", "Choose progress over perfection.",
         16, 76, section.width - 32, 16);
    const button = f.createFrame();
    root.appendChild(button);
    button.name = "Add entry"; button.resize(48, 48);
    button.x = 24; button.y = input.height - 72;
    button.cornerRadius = 24; button.fills = solid(1, 0.42, 0.09);
    rectangle(button, "Plus horizontal", 15, 23, 18, 2, solid(1, 1, 1));
    rectangle(button, "Plus vertical", 23, 15, 2, 18, solid(1, 1, 1));

    root.visible = true;
    f.currentPage.selection = [root];
    f.viewport.scrollAndZoomIntoView([root]);
    const nodes = root.findAll();
    return { id: root.id, name: root.name, width: root.width, height: root.height,
      textLayers: nodes.filter(n => n.type === "TEXT").length,
      descendants: nodes.length, sourceId: source.id };
  } catch (error) {
    root.remove();
    throw error;
  }
}, {
  pageId: "<observed page ID>", sourceId: "<observed source ID>",
  outputName: "<unique requested output name>", width: 390, height: 844
});
await page.shot({ type: "jpeg", maxEdge: 1600, quality: 70 });
return result;
```

Append children to their intended parent before setting relative coordinates. `x` and `y` are parent-local; `absoluteBoundingBox` is page-space. The example restricts the source to a top-level node so it does not mix these coordinate systems. For nested sources, place the output using a suitable top-level ancestor or an explicit transform. Avoid changing original nodes to simplify positioning.

Creation is not transactional. The catch removes only the new root owned by this run. On an interrupted or timed-out run, inspect the output before rerunning. Do not remove someone else's frame. Preserve the original source and any selection/viewport state that the task did not authorize changing; creation tasks normally select and reveal their new output.

## Rebuild screenshots as editable UI

1. Inspect the selected node and export its image at readable resolution. Identify the app content bounds separately from any phone bezel, notch, status bar, and home indicator.
2. Read visible copy, spacing, colors, and hierarchy from that image. Use a native frame with the requested iOS or other target dimensions. A Figma FRAME with iOS-sized geometry is sufficient; do not draw device chrome unless requested.
3. Create semantic section/card frames and native TEXT, RECTANGLE, ELLIPSE, and VECTOR layers. Draw simple icons as shapes or `vectorPaths`. Do not place the whole screenshot underneath an apparent editable overlay and call that reconstruction.
4. Use image fills only for actual photos or artwork. Crop avatar photos from the source if appropriate; keep text, controls, and card surfaces native. Prefer already-installed native tools, such as macOS `sips`, over installing an imaging library.
5. Load available fonts, build the new root out of view, clean it up on an error, then select/reveal it. Inspect the export or viewport for clipping, wrapping, missing content, and major differences against the source.
6. Report approximated fonts, icons, illegible/occluded copy, and raster photo layers. Do not claim pixel-perfect fidelity without a comparison. Stop when the requested result and review handoff exist.

`exportAsync` renders the selected node including its applied crop/transform. If original image bytes rather than that rendering are required, an IMAGE paint's `imageHash` can be resolved with `f.getImageByHash(hash)` and `await image.getBytesAsync()`. Keep those bytes private.

An image-fill fragment for a guarded native ellipse or rectangle `photoNode`:

```js
const image = f.createImage(new Uint8Array(input.photoBytes));
photoNode.fills = [{ type: "IMAGE", imageHash: image.hash, scaleMode: "FILL" }];
```

Read photo bytes on their owning machine and pass a JSON number array as `input.photoBytes`. `Buffer` is available in the runner, not inside `page.evaluate`.

## Reuse, auto layout, and components

Prefer an existing component or a clone over redrawing native content when the task permits it. `node.clone()` makes a copy; set its name/position and record its ID. Never `remove()` an existing node without explicit deletion authority.

For an owned FRAME with children, set `layoutMode = "VERTICAL"` or `"HORIZONTAL"`, `itemSpacing`, and `paddingTop`, `paddingRight`, `paddingBottom`, `paddingLeft`. Use `primaryAxisSizingMode = "AUTO"` for content-sized primary dimensions, or `"FIXED"` with `resize` for fixed dimensions. Auto layout determines normal children's positions; do not combine it with manual `x/y` placement unless using intentional absolute-positioned children. Add auto layout only when needed, not as a hidden extra deliverable.

For a reusable design, `f.createComponent()` creates a native component container. Populate it as a frame, then `component.createInstance()` makes an instance. Do not imply that the basic reconstruction recipe creates a component system or responsive layout. Probe these methods once before a task that needs them. For complex variants or an unfamiliar property, consult the specific official API entry rather than researching a new automation stack.

## Export and retain a receipt

This runner script exports a guarded node to its session storage, then captures the visible editor. Append it after the usual existing-page attachment code.

```js
const bytes = await page.evaluate(async input => {
  const f = window.figma;
  if (!f?.currentPage || f.currentPage.id !== input.pageId) {
    throw new Error("Export page changed");
  }
  const node = await f.getNodeByIdAsync(input.nodeId);
  if (!node || !f.currentPage.findOne(n => n.id === node.id) ||
      typeof node.exportAsync !== "function") throw new Error("Export target unavailable");
  const data = await node.exportAsync({
    format: "JPG", constraint: { type: "SCALE", value: 2 }
  });
  return Array.from(data);
}, { pageId: "<observed page ID>", nodeId: "<observed output ID>" });
await saveFile("figma-export.jpg", Buffer.from(bytes));
await page.shot({ type: "jpeg", maxEdge: 1600, quality: 70 });
return { savedFile: "figma-export.jpg", byteLength: bytes.length };
```

For transparent output use `format: "PNG"`; for native vector export use `format: "SVG"` on an exportable node. Those exports are saved files, not `page.shot` attachments, which must be JPEG. Large exports returned through `evaluate` can exceed the runner's text limit, observed as 512 KB. Reduce scale or export a smaller relevant node rather than printing large byte arrays.

`saveFile` confines writes to session storage. Its reported path may be redacted as `[session storage]/tmp/figma-export.jpg`. The screenshot's actual remote image path identifies that same session temporary directory; use its directory with the saved export basename if needed. Retrieve through `bb file read` on the browser host before stopping the session. Never assume a remote path exists on the agent's filesystem.

For a layer rename, `page.waitForFunction` can wait for the visible Layers tree text before taking the receipt. For created UI, the revealed frame plus an inspected export proves appearance; native node types corroborate editability. Neither a successful API return nor a layer count replaces observing the requested design.

## Public references and limits

- [Figma Plugin API](https://developers.figma.com/docs/plugins/api/figma/) for specific missing methods.
- [BB browser-automation](https://github.com/get-bb/bb/blob/main/plugins/browser-automation/README.md) for an actual CLI compatibility error.
- [BB multi-device setup](https://github.com/get-bb/bb/blob/main/docs/multiple-devices.md) for a missing connected desktop prerequisite.

These are fallback references, not required setup reading. The browser transport and native-frame recipe were exercised on a real editor. Component and auto-layout notes describe the Plugin API contract; they do not assert that every client exposes every method. If the live global lacks a needed method, report that constraint instead of accessing private editor internals.
