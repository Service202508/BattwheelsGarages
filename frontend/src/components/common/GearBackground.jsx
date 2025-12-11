import React, { useMemo } from 'react';

/**
 * GearBackground Component
 * Premium, futuristic rotating gears background for Battwheels Garages
 * - Ultra-subtle with 30% opacity
 * - Slow rotation with fade in/out
 * - Behind all content (z-index: -1)
 * - Responsive (40% scale on mobile)
 */

// SVG Gear Path Generator
const generateGearPath = (teeth, innerRadius, outerRadius, toothHeight) => {
  const points = [];
  const angleStep = (2 * Math.PI) / teeth;
  const toothAngle = angleStep * 0.3;
  
  for (let i = 0; i < teeth; i++) {
    const angle = i * angleStep;
    
    // Inner point before tooth
    points.push({
      x: Math.cos(angle - toothAngle) * innerRadius,
      y: Math.sin(angle - toothAngle) * innerRadius
    });
    
    // Outer tooth left
    points.push({
      x: Math.cos(angle - toothAngle * 0.5) * outerRadius,
      y: Math.sin(angle - toothAngle * 0.5) * outerRadius
    });
    
    // Outer tooth right
    points.push({
      x: Math.cos(angle + toothAngle * 0.5) * outerRadius,
      y: Math.sin(angle + toothAngle * 0.5) * outerRadius
    });
    
    // Inner point after tooth
    points.push({
      x: Math.cos(angle + toothAngle) * innerRadius,
      y: Math.sin(angle + toothAngle) * innerRadius
    });
  }
  
  return points.map((p, i) => `${i === 0 ? 'M' : 'L'} ${p.x + outerRadius + toothHeight} ${p.y + outerRadius + toothHeight}`).join(' ') + ' Z';
};

// Single Gear SVG Component
const GearSVG = ({ size, teeth, color, className }) => {
  const outerRadius = size / 2 - 5;
  const innerRadius = outerRadius * 0.75;
  const toothHeight = outerRadius * 0.15;
  const centerHoleRadius = outerRadius * 0.25;
  
  const gearPath = useMemo(() => 
    generateGearPath(teeth, innerRadius, outerRadius, toothHeight),
    [teeth, innerRadius, outerRadius, toothHeight]
  );
  
  return (
    <svg 
      width={size} 
      height={size} 
      viewBox={`0 0 ${size} ${size}`}
      className={className}
      style={{ filter: 'blur(1px)' }}
    >
      <defs>
        <linearGradient id={`gearGrad-${size}-${teeth}`} x1="0%" y1="0%" x2="100%" y2="100%">
          <stop offset="0%" stopColor="#1BAE70" stopOpacity="0.35" />
          <stop offset="50%" stopColor="#0C8F57" stopOpacity="0.3" />
          <stop offset="100%" stopColor="#1BAE70" stopOpacity="0.25" />
        </linearGradient>
        <filter id={`gearShadow-${size}`} x="-20%" y="-20%" width="140%" height="140%">
          <feDropShadow dx="0" dy="0" stdDeviation="3" floodColor="#1BAE70" floodOpacity="0.2"/>
        </filter>
      </defs>
      <g filter={`url(#gearShadow-${size})`}>
        <path 
          d={gearPath} 
          fill={`url(#gearGrad-${size}-${teeth})`}
          stroke="#1BAE70"
          strokeWidth="0.5"
          strokeOpacity="0.15"
        />
        {/* Center hole */}
        <circle 
          cx={size / 2} 
          cy={size / 2} 
          r={centerHoleRadius} 
          fill="transparent"
          stroke="#0C8F57"
          strokeWidth="2"
          strokeOpacity="0.2"
        />
        {/* Inner ring */}
        <circle 
          cx={size / 2} 
          cy={size / 2} 
          r={centerHoleRadius * 1.8} 
          fill="none"
          stroke="#1BAE70"
          strokeWidth="1"
          strokeOpacity="0.15"
        />
      </g>
    </svg>
  );
};

// Gear configurations for different positions
const gearConfigs = [
  // Small gears
  { size: 60, teeth: 8, duration: '18s', fadeDelay: '0s', position: { top: '15%', left: '5%' }, direction: 'normal' },
  { size: 50, teeth: 6, duration: '22s', fadeDelay: '3s', position: { top: '60%', right: '8%' }, direction: 'reverse' },
  { size: 45, teeth: 7, duration: '25s', fadeDelay: '6s', position: { bottom: '20%', left: '12%' }, direction: 'normal' },
  // Medium gears
  { size: 90, teeth: 10, duration: '15s', fadeDelay: '2s', position: { top: '35%', right: '3%' }, direction: 'reverse' },
  { size: 80, teeth: 9, duration: '20s', fadeDelay: '5s', position: { bottom: '30%', right: '15%' }, direction: 'normal' },
  { size: 70, teeth: 8, duration: '12s', fadeDelay: '8s', position: { top: '70%', left: '3%' }, direction: 'reverse' },
];

const GearBackground = ({ variant = 'default' }) => {
  // Different gear configurations for different pages
  const getGearSubset = () => {
    switch (variant) {
      case 'home':
        return gearConfigs;
      case 'services':
        return [gearConfigs[0], gearConfigs[2], gearConfigs[3], gearConfigs[5]];
      case 'industries':
        return [gearConfigs[1], gearConfigs[2], gearConfigs[4], gearConfigs[5]];
      case 'blog':
        return [gearConfigs[0], gearConfigs[1], gearConfigs[3], gearConfigs[4]];
      case 'contact':
        return [gearConfigs[0], gearConfigs[2], gearConfigs[4]];
      case 'battwheels-os':
        return [gearConfigs[1], gearConfigs[3], gearConfigs[4], gearConfigs[5]];
      default:
        return gearConfigs.slice(0, 4);
    }
  };

  const gears = getGearSubset();

  return (
    <div 
      className="fixed inset-0 pointer-events-none overflow-hidden"
      style={{ zIndex: -1 }}
      aria-hidden="true"
    >
      {gears.map((gear, index) => (
        <div
          key={index}
          className="absolute gear-container"
          style={{
            ...gear.position,
            '--rotation-duration': gear.duration,
            '--fade-delay': gear.fadeDelay,
            '--rotation-direction': gear.direction,
          }}
        >
          <div 
            className="gear-rotate"
            style={{
              animation: `gearRotate ${gear.duration} linear infinite ${gear.direction}`,
            }}
          >
            <div 
              className="gear-fade"
              style={{
                animation: `gearFade 12s ease-in-out infinite`,
                animationDelay: gear.fadeDelay,
              }}
            >
              <GearSVG 
                size={gear.size} 
                teeth={gear.teeth}
                color="#1BAE70"
                className="transform scale-100 md:scale-100 scale-[0.6]"
              />
            </div>
          </div>
        </div>
      ))}
      
      {/* Styles */}
      <style>{`
        @keyframes gearRotate {
          from {
            transform: rotate(0deg);
          }
          to {
            transform: rotate(360deg);
          }
        }
        
        @keyframes gearFade {
          0%, 100% {
            opacity: 0.3;
          }
          50% {
            opacity: 0.08;
          }
        }
        
        .gear-container {
          will-change: transform;
        }
        
        .gear-rotate {
          will-change: transform;
        }
        
        .gear-fade {
          will-change: opacity;
        }
        
        /* Mobile: Scale down gears by 40% */
        @media (max-width: 768px) {
          .gear-container svg {
            transform: scale(0.6);
          }
        }
        
        /* Reduce motion for accessibility */
        @media (prefers-reduced-motion: reduce) {
          .gear-rotate {
            animation: none !important;
          }
          .gear-fade {
            animation: none !important;
            opacity: 0.2 !important;
          }
        }
      `}</style>
    </div>
  );
};

export default GearBackground;
