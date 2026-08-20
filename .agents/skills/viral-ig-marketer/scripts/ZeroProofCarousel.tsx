import { AbsoluteFill, useCurrentFrame } from "remotion";

/**
 * ZeroProofCarousel — brand renderer only.
 *
 * This composition owns ONLY the visual style (colors, typography, layout).
 * The AGENT owns all content decisions: what to write, how many slides, structure.
 *
 * Primary input: `slides` array — agent-generated, any length.
 * Contract metadata (topic, angle, etc.) are optional context; they do NOT
 * prescribe slide structure or count.
 *
 * Props:
 *   slides         — REQUIRED. Array of slide content objects. Length = slide count.
 *   visualStyle    — "light" (default, white bg) | "green" (brand green bg for all slides)
 *
 *   // Optional metadata (not used for rendering — for logging/context only)
 *   topic?
 *   targetAudience?
 *   angle?
 *   cta?
 */

export interface Slide {
  headline: string;
  body?: string;
  accent?: string;
  variant?: "light" | "green"; // per-slide bg — agent can vary per slide
}

export interface ZeroProofCarouselProps {
  slides: Slide[];
  visualStyle?: "light" | "green";
  // metadata (not rendered — context only)
  topic?: string;
  targetAudience?: string;
  angle?: string;
  cta?: string;
}

const BRAND = {
  green: "#34D634",
  white: "#FFFFFF",
  black: "#0D0D0D",
  gray: "#6E6E73",
  lightGray: "#F2F2F7",
};

export const ZeroProofCarousel: React.FC<ZeroProofCarouselProps> = (props) => {
  const frame = useCurrentFrame();
  const slides = props.slides ?? [];
  const totalSlides = slides.length;
  const slideIndex = Math.min(frame, totalSlides - 1);
  const slide = slides[slideIndex];

  if (!slide) return null;

  const isGreen = slide.variant === "green" || props.visualStyle === "green";
  const bg = isGreen ? BRAND.green : BRAND.white;
  const textPrimary = isGreen ? BRAND.black : BRAND.black;
  const textSecondary = isGreen ? "rgba(0,0,0,0.6)" : BRAND.gray;
  const accentColor = isGreen ? BRAND.black : BRAND.green;
  const dotActive = isGreen ? BRAND.black : BRAND.green;
  const dotInactive = isGreen ? "rgba(0,0,0,0.2)" : BRAND.lightGray;
  const dividerColor = isGreen ? "rgba(0,0,0,0.12)" : BRAND.lightGray;

  return (
    <AbsoluteFill
      style={{
        backgroundColor: bg,
        fontFamily: "-apple-system, BlinkMacSystemFont, 'SF Pro Display', 'Helvetica Neue', sans-serif",
      }}
    >
      {/* Top bar */}
      <div style={{
        position: "absolute",
        top: 56,
        left: 72,
        right: 72,
        display: "flex",
        justifyContent: "space-between",
        alignItems: "center",
      }}>
        <span style={{
          color: isGreen ? "rgba(0,0,0,0.5)" : BRAND.gray,
          fontSize: 26,
          fontWeight: 500,
          letterSpacing: 2,
          textTransform: "uppercase" as const,
        }}>
          Zero Proof
        </span>
        <span style={{
          color: isGreen ? "rgba(0,0,0,0.5)" : BRAND.gray,
          fontSize: 26,
          fontWeight: 400,
        }}>
          {slideIndex + 1} / {totalSlides}
        </span>
      </div>

      {/* Divider */}
      <div style={{
        position: "absolute",
        top: 112,
        left: 72,
        right: 72,
        height: 1,
        backgroundColor: dividerColor,
      }} />

      {/* Main content */}
      <div style={{
        position: "absolute",
        top: 0,
        bottom: 0,
        left: 72,
        right: 72,
        display: "flex",
        flexDirection: "column",
        justifyContent: "center",
        gap: 36,
      }}>
        {slide.headline ? (
          <div style={{
            color: textPrimary,
            fontSize: slideIndex === 0 ? 80 : 64,
            fontWeight: 700,
            lineHeight: 1.1,
            letterSpacing: -1.5,
          }}>
            {slide.headline}
          </div>
        ) : null}
        {slide.body ? (
          <div style={{
            color: textSecondary,
            fontSize: 34,
            lineHeight: 1.65,
            fontWeight: 400,
          }}>
            {slide.body}
          </div>
        ) : null}
        {slide.accent ? (
          <div style={{
            color: accentColor,
            fontSize: 30,
            fontWeight: 600,
            letterSpacing: 0.5,
          }}>
            {slide.accent}
          </div>
        ) : null}
      </div>

      {/* Bottom dots — slide count driven by agent's slides array */}
      <div style={{
        position: "absolute",
        bottom: 56,
        left: 0,
        right: 0,
        display: "flex",
        justifyContent: "center",
        gap: 14,
        alignItems: "center",
      }}>
        {slides.map((_, i) => (
          <div
            key={i}
            style={{
              width: i === slideIndex ? 36 : 10,
              height: 10,
              borderRadius: 5,
              backgroundColor: i === slideIndex ? dotActive : dotInactive,
            }}
          />
        ))}
      </div>
    </AbsoluteFill>
  );
};
