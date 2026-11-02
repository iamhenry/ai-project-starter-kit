# Verification Gate: Visual Convergence Loop

Use when the task changes visible UI against a reference. First ask how the reference relates to the screenshot, because a pixel score only answers "same pixels?":
- Same grid and intent (a prior build, an approved screenshot): run the loop below.
- Same intent, different scale or renderer (a Figma export): align the grid first, then run the loop ("Reference of a different size").
- Same content, different layout (a web page vs an app screen): a pixel score will not tell right from wrong; see "Same content, different layout".

1. Capture a baseline of the target screen at or before the current state.
2. Capture the current state with the platform tool, then diff it against the ideal state with the pixel diff tool below. When already driving a device through argent, its `screenshot-diff` may capture and diff in one call.
3. If the changed-pixel ratio exceeds the declared tolerance, the diff image names where to fix next. Route that back to implementation and re-diff after the fix.
4. Stop when the ratio is within tolerance or the remaining diffs are declared acceptable (for example font-version rendering). Record the final ratio and diff image as Observable evidence. If the images are identical no diff file is written; record the exit code and the "identical" line as the receipt.

Tolerance is set by the Verification Target, not invented here. The diff image supports the verdict; it never replaces the Primary Flow proof.

## Pixel diff tool

For any two same-size PNGs, use `blazediff-cli` instead of a custom script (~0.1 s per full-size screenshot).

```
blazediff-cli interpret before.png after.png <evidence-dir>/diff.png
```

If `command -v blazediff-cli` finds nothing, install it (macOS and Linux, x64 and arm64; needs npm). This reference pre-authorizes the install:

```
npm i -g @blazediff/cli
```

If global install is not allowed, prefix the command with `npx -y @blazediff/cli` instead. If neither works, return `BLOCKED` naming the install step; do not write a custom diff script.

- Exit 0 means identical (imperceptible color noise is ignored). Exit 1 means different, even by 0.02%. Different image sizes is an error, not a diff.
- Judge against the Target's tolerance using the printed %, not the exit code. Use the exit code alone only when the tolerance is zero.
- On a difference it prints a summary and a region list (change type, size, position, % of image). Read that first; open the PNG only to confirm.
- Swap `interpret` for nothing to get just the changed-pixel count and %. `-t <0-1>` is the per-pixel color threshold (default 0.1), separate from the Target's changed-pixel tolerance.

Rules:
- When the claim is about color or shade, use `-t 0`. The default hides shifts of about 20/255 or less over flat areas; keep it for layout and text claims.
- Write `diff.png` into the evidence directory, not temp.
- Compare like with like (same device, state, and size), or align the grid first.
- Remove noise before the diff, not in it: freeze clocks and status bars, seed data, or crop the noisy area from both images. The tool has no ignore-region option.

## Reference of a different size (Figma export, mock, older device)

The tool only compares images of the same size (`interpret` exits 2 otherwise). So first put both on the same pixel grid, by whatever route is cheapest:

- Export or capture the reference at the screenshot's size (a Figma export size can be set by width, such as `1179w`).
- Or resize the reference to the screenshot's width (`sips --resampleWidth <w> in.png --out out.png` on macOS, `magick in.png -resize <w>x out.png` on Linux), then crop to equal heights.
- Crop anything one side lacks, such as a status bar, home indicator, or device frame, or keep it on both sides.

Resizing and different text rendering add a noise floor, so use a looser `-t` (about 0.3 worked in a trial), find the floor by diffing a screenshot against a resized copy of itself, and read only the regions clearly above it. Use the result to see whether the UI is converging on the reference, then confirm by eye.

## Same content, different layout (web page vs app screen)

Text reflows, so slices do not line up and a wrong pairing scores about as well as a right one. In a trial on a web page vs a reader screen, the right pairing beat a wrong one only 7 of 12 times (pixel, SSIM) and 5 of 12 (GMSD). Do not use a pixel or similarity score as the verdict here. Instead:

- Compare structure: the reference's outline (DOM or accessibility tree) against the app's, element by element.
- Put both at matching scroll positions side by side and judge by eye.
- Use `blazediff-cli` between app candidates (before vs after the same app) to see what moved.
