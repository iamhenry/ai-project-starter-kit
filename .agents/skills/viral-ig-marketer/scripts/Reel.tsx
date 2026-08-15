import React from 'react';
import {
  useCurrentFrame,
  useVideoConfig,
  Img,
  Audio,
  staticFile,
  spring,
  interpolate,
  Sequence,
} from 'remotion';
import {TransitionSeries, linearTiming} from '@remotion/transitions';
import {fade} from '@remotion/transitions/fade';

export type ReelProps = {
  images: string[];        // URLs or staticFile paths (4 images for content slides)
  hookText: string;        // Hook overlay text (slide 1)
  sceneTexts: string[];    // Text overlay per content slide (slides 2-5)
  ctaText: string;         // CTA text (slide 6)
  audioFile: string;       // Filename in public/ folder
  secondsPerScene: number; // Duration per image scene
};

const Scene: React.FC<{
  src: string;
  text?: string;
  textPosition?: 'top' | 'center' | 'bottom';
  isHook?: boolean;
}> = ({src, text, textPosition = 'bottom', isHook}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();

  // Ken Burns: subtle zoom 100% -> 112% over the scene
  const scale = interpolate(frame, [0, 3 * fps], [1, 1.12], {
    extrapolateRight: 'clamp',
  });

  // Text spring animation
  const textSpring = spring({
    frame: frame - 5,
    fps,
    config: {damping: 200},
  });

  const textOpacity = interpolate(textSpring, [0, 1], [0, 1]);
  const textY = interpolate(textSpring, [0, 1], [30, 0]);

  return (
    <div style={{
      width: '100%',
      height: '100%',
      overflow: 'hidden',
      position: 'relative',
      backgroundColor: '#000',
    }}>
      <Img
        src={src}
        style={{
          width: '100%',
          height: '100%',
          objectFit: 'cover',
          transform: `scale(${scale})`,
        }}
      />
      {text && (
        <div style={{
          position: 'absolute',
          left: 0,
          right: 0,
          ...(isHook
            ? {top: '50%', transform: `translateY(-50%) translateY(${textY}px)`}
            : {bottom: 160, transform: `translateY(${textY}px)`}),
          display: 'flex',
          justifyContent: 'center',
          padding: '0 48px',
          opacity: textOpacity,
        }}>
          <div style={{
            background: isHook
              ? 'linear-gradient(135deg, rgba(0,0,0,0.85), rgba(0,0,0,0.7))'
              : 'linear-gradient(135deg, rgba(0,0,0,0.8), rgba(0,0,0,0.6))',
            borderRadius: 20,
            padding: isHook ? '32px 48px' : '20px 36px',
            maxWidth: 920,
            backdropFilter: 'blur(8px)',
          }}>
            <div style={{
              color: '#fff',
              fontSize: isHook ? 54 : 40,
              fontWeight: isHook ? 800 : 700,
              textAlign: 'center',
              lineHeight: 1.3,
              fontFamily: 'sans-serif',
              textShadow: '0 2px 12px rgba(0,0,0,0.6)',
            }}>
              {text}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

const CtaScene: React.FC<{text: string}> = ({text}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();

  const scale = spring({
    frame,
    fps,
    config: {damping: 12, stiffness: 80},
  });

  const opacity = interpolate(frame, [0, 0.5 * fps], [0, 1], {
    extrapolateRight: 'clamp',
  });

  return (
    <div style={{
      width: '100%',
      height: '100%',
      backgroundColor: '#0a0a0a',
      display: 'flex',
      flexDirection: 'column',
      alignItems: 'center',
      justifyContent: 'center',
      padding: '0 80px',
    }}>
      <div style={{
        opacity,
        transform: `scale(${scale})`,
        textAlign: 'center',
      }}>
        <div style={{
          color: '#fff',
          fontSize: 48,
          fontWeight: 700,
          lineHeight: 1.4,
          fontFamily: 'sans-serif',
          marginBottom: 40,
        }}>
          {text}
        </div>
        <div style={{
          color: '#4ade80',
          fontSize: 36,
          fontWeight: 600,
          fontFamily: 'sans-serif',
        }}>
          ⬇ Link in bio
        </div>
      </div>
    </div>
  );
};

export const Reel: React.FC<ReelProps> = ({
  images,
  hookText,
  sceneTexts = [],
  ctaText,
  audioFile,
  secondsPerScene,
}) => {
  const {fps} = useVideoConfig();
  const sceneDur = secondsPerScene * fps;
  const transitionDur = Math.round(0.5 * fps);
  const ctaDur = 3 * fps;

  return (
    <div style={{width: 1080, height: 1920, position: 'relative'}}>
      <Audio src={staticFile(audioFile)} />

      <TransitionSeries>
        {images.map((img, i) => {
          const isFirst = i === 0;
          const isLast = i === images.length - 1;
          const src = img.startsWith('http') ? img : staticFile(img);

          // Slide 1 = hook text, slides 2-5 = sceneTexts[0..3]
          const text = isFirst ? hookText : (sceneTexts[i - 1] || undefined);

          return (
            <React.Fragment key={i}>
              <TransitionSeries.Sequence durationInFrames={sceneDur}>
                <Scene
                  src={src}
                  text={text}
                  isHook={isFirst}
                />
              </TransitionSeries.Sequence>
              {!isLast && (
                <TransitionSeries.Transition
                  presentation={fade()}
                  timing={linearTiming({durationInFrames: transitionDur})}
                />
              )}
            </React.Fragment>
          );
        })}

        <TransitionSeries.Transition
          presentation={fade()}
          timing={linearTiming({durationInFrames: transitionDur})}
        />
        <TransitionSeries.Sequence durationInFrames={ctaDur}>
          <CtaScene text={ctaText} />
        </TransitionSeries.Sequence>
      </TransitionSeries>
    </div>
  );
};
