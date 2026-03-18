import {Composition} from 'remotion';
import {Reel, ReelProps} from './Reel';

export const RemotionRoot: React.FC = () => {
  return (
    <Composition
      id="Reel"
      component={Reel}
      durationInFrames={300} // overridden by calculateMetadata
      fps={30}
      width={1080}
      height={1920}
      defaultProps={{
        images: [],
        hookText: 'Your hook text here',
        ctaText: 'Download Zero Proof — link in bio',
        audioFile: 'calm-reflective.mp3',
        secondsPerScene: 3,
      } satisfies ReelProps}
      calculateMetadata={({props}) => {
        const sceneDur = props.secondsPerScene * 30;
        const transitionDur = 15; // 0.5s
        const totalScenes = props.images.length;
        const ctaDur = 90; // 3s
        const dur = totalScenes * sceneDur - (totalScenes - 1) * transitionDur + ctaDur;
        return {durationInFrames: dur};
      }}
    />
  );
};
