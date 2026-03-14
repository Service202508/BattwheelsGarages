import React from 'react';
import { Zap } from 'lucide-react';

const sizes = {
  xs: { box: 28, icon: 14, terminalText: 8, terminalOffset: 2 },
  sm: { box: 36, icon: 18, terminalText: 10, terminalOffset: 2 },
  md: { box: 40, icon: 20, terminalText: 11, terminalOffset: 3 },
  lg: { box: 48, icon: 24, terminalText: 13, terminalOffset: 3 },
};

export default function BattwheelsLogo({ size = 'md', variant = 'solid', className = '' }) {
  const s = sizes[size] || sizes.md;

  const isSolid = variant === 'solid';

  const containerStyle = {
    width: s.box,
    height: s.box,
    position: 'relative',
    display: 'inline-flex',
    alignItems: 'center',
    justifyContent: 'center',
    borderRadius: 6,
    flexShrink: 0,
    backgroundColor: isSolid ? '#CBFF00' : 'rgba(255,255,255,0.05)',
    border: isSolid ? 'none' : '1.5px solid #CBFF00',
  };

  const iconColor = isSolid ? '#000000' : '#CBFF00';

  const terminalBase = {
    position: 'absolute',
    fontFamily: 'JetBrains Mono, monospace',
    fontWeight: 700,
    lineHeight: 1,
    color: isSolid ? '#000000' : '#CBFF00',
    fontSize: s.terminalText,
    userSelect: 'none',
  };

  return (
    <span
      data-testid="battwheels-logo"
      className={className}
      style={containerStyle}
      aria-label="Battwheels logo"
    >
      {/* Positive terminal — top-left */}
      <span style={{ ...terminalBase, top: s.terminalOffset, left: s.terminalOffset + 1 }}>
        +
      </span>

      {/* Bolt */}
      <Zap
        size={s.icon}
        fill={iconColor}
        color={iconColor}
        strokeWidth={0}
        style={{ position: 'relative', zIndex: 1 }}
      />

      {/* Negative terminal — bottom-right */}
      <span style={{ ...terminalBase, bottom: s.terminalOffset, right: s.terminalOffset + 2 }}>
        ·
      </span>
    </span>
  );
}
