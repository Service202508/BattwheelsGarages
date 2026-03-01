/**
 * Battwheels OS — Theme Color Constants
 *
 * Use these ONLY where inline hex is unavoidable:
 *   - Chart libraries (Recharts, Chart.js) that require hex/rgb strings
 *   - SVG fill/stroke attributes
 *   - Dynamic canvas drawing
 *
 * For ALL other cases, use Tailwind classes: bg-bw-volt, text-bw-white, etc.
 */

export const colors = {
  volt:       '#C8FF00',
  voltHover:  '#d4ff1a',
  white:      '#F4F6F0',
  black:      '#080C0F',
  offBlack:   '#0D1317',
  panel:      '#111820',
  card:       '#192330',
  green:      '#22C55E',
  greenHover: '#16a34a',
  red:        '#FF3B2F',
  orange:     '#FF8C00',
  amber:      '#EAB308',
  blue:       '#3B9EFF',
  blueHover:  '#2A8EEE',
  teal:       '#1AFFE4',
  purple:     '#8B5CF6',
};

/** Opacity helpers for chart backgrounds */
export const withAlpha = (hex, alpha) => {
  const r = parseInt(hex.slice(1, 3), 16);
  const g = parseInt(hex.slice(3, 5), 16);
  const b = parseInt(hex.slice(5, 7), 16);
  return `rgba(${r},${g},${b},${alpha})`;
};
