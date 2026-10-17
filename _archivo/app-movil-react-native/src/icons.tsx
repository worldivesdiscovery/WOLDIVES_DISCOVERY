// Stroke icons (24 px grid), drawn with react-native-svg. No emoji, no icon font.
import React from 'react';
import Svg, { Circle, Path, Rect } from 'react-native-svg';

const P: Record<string, React.ReactNode[]> = {
  home: [<Path key="a" d="M3 10.5 12 3l9 7.5" />, <Path key="b" d="M5 9.5V21h14V9.5" />],
  map: [<Path key="a" d="M9 4 3 6v14l6-2 6 2 6-2V4l-6 2-6-2z" />, <Path key="b" d="M9 4v14" />, <Path key="c" d="M15 6v14" />],
  ticket: [<Path key="a" d="M3 8a2 2 0 0 0 2-2h14a2 2 0 0 0 2 2v2a2 2 0 0 0 0 4v2a2 2 0 0 0-2 2H5a2 2 0 0 0-2-2v-2a2 2 0 0 0 0-4z" />],
  user: [<Circle key="a" cx="12" cy="8" r="4" />, <Path key="b" d="M4 21a8 8 0 0 1 16 0" />],
  bell: [<Path key="a" d="M6 8a6 6 0 0 1 12 0c0 7 3 9 3 9H3s3-2 3-9" />, <Path key="b" d="M10.3 21a1.94 1.94 0 0 0 3.4 0" />],
  clock: [<Circle key="a" cx="12" cy="12" r="9" />, <Path key="b" d="M12 7v5l3 2" />],
  pin: [<Path key="a" d="M12 21s-7-6.2-7-12a7 7 0 0 1 14 0c0 5.8-7 12-7 12z" />, <Circle key="b" cx="12" cy="9" r="2.5" />],
  wave: [<Path key="a" d="M2 12c2 0 2-2 4-2s2 2 4 2 2-2 4-2 2 2 4 2 2-2 4-2" />, <Path key="b" d="M2 17c2 0 2-2 4-2s2 2 4 2 2-2 4-2 2 2 4 2 2-2 4-2" />],
  check: [<Path key="a" d="M20 6 9 17l-5-5" />],
  checkCircle: [<Circle key="a" cx="12" cy="12" r="9" />, <Path key="b" d="M8.5 12.5l2.3 2.3 4.7-5" />],
  alert: [<Circle key="a" cx="12" cy="12" r="9" />, <Path key="b" d="M12 8v5" />, <Path key="c" d="M12 16.5h.01" />],
  info: [<Circle key="a" cx="12" cy="12" r="9" />, <Path key="b" d="M12 16v-4" />, <Path key="c" d="M12 8h.01" />],
  plus: [<Path key="a" d="M12 5v14M5 12h14" />],
  minus: [<Path key="a" d="M5 12h14" />],
  close: [<Path key="a" d="M18 6 6 18M6 6l12 12" />],
  chevron: [<Path key="a" d="m9 18 6-6-6-6" />],
  back: [<Path key="a" d="m15 18-6-6 6-6" />],
  pen: [<Path key="a" d="M12 20h9" />, <Path key="b" d="M16.5 3.5a2.1 2.1 0 0 1 3 3L7 19l-4 1 1-4z" />],
  scan: [<Path key="a" d="M4 8V5a1 1 0 0 1 1-1h3M16 4h3a1 1 0 0 1 1 1v3M20 16v3a1 1 0 0 1-1 1h-3M8 20H5a1 1 0 0 1-1-1v-3" />, <Path key="b" d="M8 12h8" />],
  sun: [<Circle key="a" cx="12" cy="12" r="4" />, <Path key="b" d="M12 2v2M12 20v2M4.9 4.9l1.4 1.4M17.7 17.7l1.4 1.4M2 12h2M20 12h2M4.9 19.1l1.4-1.4M17.7 6.3l1.4-1.4" />],
  calendar: [<Rect key="a" x="3" y="5" width="18" height="16" rx="2" />, <Path key="b" d="M16 3v4M8 3v4M3 10h18" />],
  users: [<Path key="a" d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2" />, <Circle key="b" cx="9" cy="7" r="4" />, <Path key="c" d="M22 21v-2a4 4 0 0 0-3-3.87" />, <Path key="d" d="M16 3.13a4 4 0 0 1 0 7.75" />],
  more: [<Circle key="a" cx="5" cy="12" r="1.5" />, <Circle key="b" cx="12" cy="12" r="1.5" />, <Circle key="c" cx="19" cy="12" r="1.5" />],
  briefcase: [<Rect key="a" x="3" y="7" width="18" height="13" rx="2" />, <Path key="b" d="M8 7V5a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2M3 13h18" />],
  wallet: [<Rect key="a" x="3" y="6" width="18" height="14" rx="2" />, <Path key="b" d="M3 10h18M16 15h2" />],
  phone: [<Path key="a" d="M22 16.9v3a2 2 0 0 1-2.2 2 19.8 19.8 0 0 1-8.6-3.1 19.5 19.5 0 0 1-6-6A19.8 19.8 0 0 1 2.1 4.2 2 2 0 0 1 4.1 2h3a2 2 0 0 1 2 1.7c.1.9.4 1.8.7 2.7a2 2 0 0 1-.5 2.1L8 9.8a16 16 0 0 0 6 6l1.3-1.3a2 2 0 0 1 2.1-.4c.9.3 1.8.6 2.7.7a2 2 0 0 1 1.7 2z" />],
  chat: [<Path key="a" d="M21 11.5a8.4 8.4 0 0 1-12.4 7.4L3 21l2-5.3A8.4 8.4 0 1 1 21 11.5z" />],
  route: [<Circle key="a" cx="6" cy="19" r="2" />, <Circle key="b" cx="18" cy="5" r="2" />, <Path key="c" d="M8 19h6a4 4 0 0 0 0-8h-4a4 4 0 0 1 0-8h6" />],
  offline: [<Path key="a" d="M2 2l20 20" />, <Path key="b" d="M8.5 16.5a5 5 0 0 1 7 0" />, <Path key="c" d="M5 12.6a10 10 0 0 1 5.2-2.5" />, <Path key="d" d="M19 12.6a10 10 0 0 0-2.3-1.6" />, <Path key="e" d="M12 20h.01" />],
  faceid: [<Path key="a" d="M4 8V6a2 2 0 0 1 2-2h2M16 4h2a2 2 0 0 1 2 2v2M20 16v2a2 2 0 0 1-2 2h-2M8 20H6a2 2 0 0 1-2-2v-2" />, <Path key="b" d="M9 10v1M15 10v1M12 10v3h-1M9.5 16a3.5 3.5 0 0 0 5 0" />],
  timer: [<Circle key="a" cx="12" cy="13" r="8" />, <Path key="b" d="M12 9v4l2 2M9 2h6" />],
  sliders: [<Path key="a" d="M4 21v-7M4 10V3M12 21v-9M12 8V3M20 21v-5M20 12V3M1 14h6M9 8h6M17 16h6" />],
};

export type IconName = keyof typeof P;

export function Icon({ name, size = 22, color, stroke = 1.9 }: { name: IconName; size?: number; color: string; stroke?: number }) {
  return (
    <Svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke={color} strokeWidth={stroke} strokeLinecap="round" strokeLinejoin="round">
      {P[name]}
    </Svg>
  );
}
