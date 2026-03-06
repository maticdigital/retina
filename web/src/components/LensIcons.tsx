/**
 * LensIcon renders a lens SVG icon with a configurable color.
 * Uses CSS mask-image so the SVG acts as a shape filled with any color.
 */
import performanceIcon from '../assets/performance_icon.svg';
import seoIcon from '../assets/seo_icon.svg';
import brandIcon from '../assets/brand_icon.svg';
import experienceIcon from '../assets/experience_icon.svg';
import conversionIcon from '../assets/conversion_icon.svg';

const LENS_ICON_SRCS: Record<string, string> = {
  performance_technical_health: performanceIcon,
  seo_ai_visibility: seoIcon,
  brand_messaging: brandIcon,
  experience_design: experienceIcon,
  conversion_strategy: conversionIcon,
};

interface LensIconProps {
  lensId: string;
  color: string;
  size?: number;
}

export function LensIcon({ lensId, color, size = 36 }: LensIconProps) {
  const src = LENS_ICON_SRCS[lensId];
  if (!src) return null;

  return (
    <div
      style={{
        width: size,
        height: size,
        flexShrink: 0,
        backgroundColor: color,
        WebkitMaskImage: `url(${src})`,
        WebkitMaskSize: 'contain',
        WebkitMaskRepeat: 'no-repeat',
        WebkitMaskPosition: 'center',
        maskImage: `url(${src})`,
        maskSize: 'contain',
        maskRepeat: 'no-repeat',
        maskPosition: 'center',
      }}
    />
  );
}
