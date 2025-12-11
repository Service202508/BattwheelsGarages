import React, { useMemo } from 'react';

/**
 * GearBackground Component
 * Premium, futuristic rotating gears background for Battwheels Garages
 * - Dark bottle green color
 * - 50% opacity
 * - Round teeth design
 * - Behind all content (z-index: -1)
 * - Responsive (40% scale on mobile)
 */

// SVG Gear Path Generator - Round teeth version
const generateRoundGearPath = (teeth, innerRadius, outerRadius) => {
  const points = [];
  const angleStep = (2 * Math.PI) / teeth;
  
  for (let i = 0; i < teeth; i++) {
    const angle = i * angleStep;
    const nextAngle = (i + 1) * angleStep;
    const midAngle = angle + angleStep / 2;
    
    // Create smooth rounded teeth using bezier-like points
    // Valley point (inner)
    points.push({
      type: 'L',
      x: Math.cos(angle) * innerRadius,
      y: Math.sin(angle) * innerRadius
    });
    
    // Rising curve control
    points.push({
      type: 'Q',
      cx: Math.cos(angle + angleStep * 0.25) * (innerRadius + (outerRadius - innerRadius) * 0.5),
      cy: Math.sin(angle + angleStep * 0.25) * (innerRadius + (outerRadius - innerRadius) * 0.5),
      x: Math.cos(midAngle) * outerRadius,
      y: Math.sin(midAngle) * outerRadius
    });
    
    // Falling curve to next valley
    points.push({
      type: 'Q',
      cx: Math.cos(midAngle + angleStep * 0.25) * (innerRadius + (outerRadius - innerRadius) * 0.5),
      cy: Math.sin(midAngle + angleStep * 0.25) * (innerRadius + (outerRadius - innerRadius) * 0.5),
      x: Math.cos(nextAngle) * innerRadius,
      y: Math.sin(nextAngle) * innerRadius
    });
  }
  
  // Build path string
  let path = `M ${points[0].x + outerRadius + 5} ${points[0].y + outerRadius + 5}`;
  
  for (let i = 0; i < points.length; i++) {
    const p = points[i];
    if (p.type === 'L') {
      path += ` L ${p.x + outerRadius + 5} ${p.y + outerRadius + 5}`;
    } else if (p.type === 'Q') {
      path += ` Q ${p.cx + outerRadius + 5} ${p.cy + outerRadius + 5} ${p.x + outerRadius + 5} ${p.y + outerRadius + 5}`;
    }
  }
  
  path += ' Z';
  return path;
};

// Single Gear SVG Component - Round teeth with dark bottle green
const GearSVG = ({ size, teeth, className, id }) => {
  const outerRadius = size / 2 - 8;
  const innerRadius = outerRadius * 0.78;
  const centerHoleRadius = outerRadius * 0.22;
  const innerRingRadius = outerRadius * 0.4;
  
  const gearPath = useMemo(() => 
    generateRoundGearPath(teeth, innerRadius, outerRadius),
    [teeth, innerRadius, outerRadius]
  );
  
  return (
    <svg 
      width={size} 
      height={size} 
      viewBox={`0 0 ${size} ${size}`}
      className={className}
      style={{ filter: 'blur(0.5px)' }}
    >
      <defs>
        {/* Dark Bottle Green Gradient */}
        <linearGradient id={`gearGrad-${id}`} x1="0%" y1="0%" x2="100%" y2="100%">
          <stop offset="0%" stopColor="#0B4D3B" stopOpacity="0.55" />
          <stop offset="50%" stopColor="#064E3B" stopOpacity="0.5" />
          <stop offset="100%" stopColor="#083D31" stopOpacity="0.45" />
        </linearGradient>
        {/* Radial gradient for depth */}
        <radialGradient id={`gearRadial-${id}`} cx="30%" cy="30%" r="70%">
          <stop offset="0%" stopColor="#0D5D47" stopOpacity="0.5" />
          <stop offset="100%" stopColor="#042F25" stopOpacity="0.5" />
        </radialGradient>
        <filter id={`gearShadow-${id}`} x="-30%" y="-30%" width="160%" height="160%">
          <feDropShadow dx="0" dy="0" stdDeviation="4" floodColor="#064E3B" floodOpacity="0.3"/>
        </filter>
      </defs>
      <g filter={`url(#gearShadow-${id})`}>
        {/* Main gear body with round teeth */}
        <path 
          d={gearPath} 
          fill={`url(#gearGrad-${id})`}
          stroke="#0B5D4A"
          strokeWidth="1"
          strokeOpacity="0.4"
        />
        {/* Inner decorative ring */}
        <circle 
          cx={size / 2} 
          cy={size / 2} 
          r={innerRingRadius} 
          fill="none"
          stroke="#0A5C48"
          strokeWidth="2"
          strokeOpacity="0.35"
        />
        {/* Center hole */}
        <circle 
          cx={size / 2} 
          cy={size / 2} 
          r={centerHoleRadius} 
          fill={`url(#gearRadial-${id})`}
          stroke="#064E3B"
          strokeWidth="1.5"
          strokeOpacity="0.4"
        />
        {/* Spokes for mechanical look */}
        {[0, 60, 120, 180, 240, 300].map((angle, i) => (
          <line
            key={i}
            x1={size / 2 + Math.cos(angle * Math.PI / 180) * centerHoleRadius}
            y1={size / 2 + Math.sin(angle * Math.PI / 180) * centerHoleRadius}
            x2={size / 2 + Math.cos(angle * Math.PI / 180) * innerRingRadius}
            y2={size / 2 + Math.sin(angle * Math.PI / 180) * innerRingRadius}
            stroke="#0A5C48"
            strokeWidth="2"
            strokeOpacity="0.25"
            strokeLinecap="round"
          />
        ))}
      </g>
    </svg>
  );
};

// Gear configurations - more gears with varied positions
const gearConfigs = [
  // Small gears
  { size: 55, teeth: 12, duration: '20s', fadeDelay: '0s', position: { top: '8%', left: '3%' }, direction: 'normal' },
  { size: 45, teeth: 10, duration: '25s', fadeDelay: '4s', position: { top: '55%', right: '5%' }, direction: 'reverse' },
  { size: 50, teeth: 11, duration: '22s', fadeDelay: '7s', position: { bottom: '15%', left: '8%' }, direction: 'normal' },
  { size: 40, teeth: 9, duration: '28s', fadeDelay: '2s', position: { top: '25%', right: '12%' }, direction: 'reverse' },
  // Medium gears
  { size: 85, teeth: 14, duration: '16s', fadeDelay: '3s', position: { top: '40%', right: '2%' }, direction: 'reverse' },
  { size: 75, teeth: 13, duration: '18s', fadeDelay: '6s', position: { bottom: '25%', right: '10%' }, direction: 'normal' },
  { size: 70, teeth: 12, duration: '14s', fadeDelay: '9s', position: { top: '75%', left: '2%' }, direction: 'reverse' },
  { size: 65, teeth: 11, duration: '21s', fadeDelay: '1s', position: { top: '12%', right: '25%' }, direction: 'normal' },
  // Additional gears for density
  { size: 60, teeth: 10, duration: '24s', fadeDelay: '5s', position: { bottom: '45%', left: '5%' }, direction: 'normal' },
  { size: 48, teeth: 9, duration: '19s', fadeDelay: '8s', position: { top: '65%', right: '20%' }, direction: 'reverse' },
];

const GearBackground = ({ variant = 'default' }) => {
  // Different gear configurations for different pages
  const getGearSubset = () => {
    switch (variant) {
      case 'home':
        return gearConfigs;
      case 'services':
        return [gearConfigs[0], gearConfigs[2], gearConfigs[4], gearConfigs[6], gearConfigs[8]];
      case 'industries':
        return [gearConfigs[1], gearConfigs[3], gearConfigs[5], gearConfigs[7], gearConfigs[9]];
      case 'blog':
        return [gearConfigs[0], gearConfigs[1], gearConfigs[4], gearConfigs[5], gearConfigs[8]];
      case 'contact':
        return [gearConfigs[0], gearConfigs[2], gearConfigs[5], gearConfigs[7]];
      case 'battwheels-os':
        return [gearConfigs[1], gearConfigs[3], gearConfigs[4], gearConfigs[6], gearConfigs[9]];
      default:
        return gearConfigs.slice(0, 6);
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
                animation: `gearFade 15s ease-in-out infinite`,
                animationDelay: gear.fadeDelay,
              }}
            >
              <GearSVG 
                size={gear.size} 
                teeth={gear.teeth}
                id={`gear-${index}`}
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
            opacity: 0.5;
          }
          50% {
            opacity: 0.25;
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
            opacity: 0.35 !important;
          }
        }
      `}</style>
    </div>
  );
};

export default GearBackground;
