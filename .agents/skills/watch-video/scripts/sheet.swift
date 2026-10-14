// sheet.swift - tiny macOS helper for watch_video.py: draws labelled contact sheets.
// Built once by watch_video.py with: swiftc -O sheet.swift -o ~/.cache/watch-video/sheet-maker
// Usage: sheet-maker <manifest.tsv> <out.jpg> <cols> <cellWidth>
// Manifest: one "imagePath<TAB>label" per line. Cells fill row by row; label is drawn above each image.
import Foundation
import CoreGraphics
import CoreText
import ImageIO

func fail(_ message: String) -> Never {
    FileHandle.standardError.write((message + "\n").data(using: .utf8)!)
    exit(1)
}

let args = CommandLine.arguments
guard args.count == 5, let cols = Int(args[3]), let cellW = Int(args[4]), cols > 0, cellW > 0 else {
    fail("usage: sheet-maker manifest.tsv out.jpg cols cellWidth")
}

guard let manifestText = try? String(contentsOfFile: args[1], encoding: .utf8) else {
    fail("cannot read manifest \(args[1])")
}

var entries: [(path: String, label: String)] = []
for line in manifestText.split(separator: "\n") {
    let parts = line.split(separator: "\t", maxSplits: 1, omittingEmptySubsequences: false)
    if parts.count == 2 { entries.append((String(parts[0]), String(parts[1]))) }
}
if entries.isEmpty { fail("manifest has no entries") }

func loadImage(_ path: String) -> CGImage? {
    guard let src = CGImageSourceCreateWithURL(URL(fileURLWithPath: path) as CFURL, nil) else { return nil }
    return CGImageSourceCreateImageAtIndex(src, 0, nil)
}

let labelH = 18
var thumbH = cellW
for e in entries {
    if let img = loadImage(e.path) {
        thumbH = Int((Double(cellW) * Double(img.height) / Double(img.width)).rounded())
        break
    }
}

let cellH = labelH + thumbH
let rowsCount = (entries.count + cols - 1) / cols
let canvasW = cols * cellW
let canvasH = rowsCount * cellH

guard let ctx = CGContext(data: nil, width: canvasW, height: canvasH, bitsPerComponent: 8, bytesPerRow: 0,
                          space: CGColorSpaceCreateDeviceRGB(),
                          bitmapInfo: CGImageAlphaInfo.noneSkipLast.rawValue) else {
    fail("cannot create canvas \(canvasW)x\(canvasH)")
}

ctx.setFillColor(CGColor(gray: 0.12, alpha: 1))
ctx.fill(CGRect(x: 0, y: 0, width: canvasW, height: canvasH))

let font = CTFontCreateWithName("Menlo-Bold" as CFString, 12, nil)
let textColor = CGColor(red: 1.0, green: 0.92, blue: 0.4, alpha: 1)

for (i, e) in entries.enumerated() {
    let col = i % cols
    let row = i / cols
    // CoreGraphics origin is bottom-left; compute the cell's bottom edge.
    let cellBottom = canvasH - (row + 1) * cellH
    let x = col * cellW

    // Label band across the top of the cell.
    ctx.setFillColor(CGColor(gray: 0.0, alpha: 1))
    ctx.fill(CGRect(x: x, y: cellBottom + thumbH, width: cellW, height: labelH))
    let attrs: [NSAttributedString.Key: Any] = [
        NSAttributedString.Key(kCTFontAttributeName as String): font,
        NSAttributedString.Key(kCTForegroundColorAttributeName as String): textColor,
    ]
    let line = CTLineCreateWithAttributedString(NSAttributedString(string: e.label, attributes: attrs))
    ctx.textPosition = CGPoint(x: CGFloat(x + 4), y: CGFloat(cellBottom + thumbH + 5))
    CTLineDraw(line, ctx)

    if let img = loadImage(e.path) {
        ctx.draw(img, in: CGRect(x: x, y: cellBottom, width: cellW, height: thumbH))
    }
}

guard let out = ctx.makeImage() else { fail("cannot render canvas") }
let outURL = URL(fileURLWithPath: args[2]) as CFURL
guard let dest = CGImageDestinationCreateWithURL(outURL, "public.jpeg" as CFString, 1, nil) else {
    fail("cannot open output \(args[2])")
}
CGImageDestinationAddImage(dest, out, [kCGImageDestinationLossyCompressionQuality: 0.72] as CFDictionary)
if !CGImageDestinationFinalize(dest) { fail("cannot write \(args[2])") }
