// Colours of the app («océano»): dark by default, light «superficie». One accent for actions.
import { Platform } from 'react-native';

export type Palette = {
  dark: boolean;
  bg: string;
  surface: string;
  surface2: string;
  line: string;
  text: string;
  muted: string;
  accent: string;
  onAccent: string;
  accentText: string;
  warn: string;
  warnBg: string;
  onWarn: string;
  sheet: string;
  dim: string;
  glow: string;
};

export const dark: Palette = {
  dark: true,
  bg: '#041526',
  surface: Platform.OS === 'ios' ? 'rgba(255,255,255,0.075)' : '#0D2A3E',
  surface2: Platform.OS === 'ios' ? 'rgba(255,255,255,0.13)' : '#143754',
  line: 'rgba(255,255,255,0.15)',
  text: '#EAF6FA',
  muted: '#A9C3CF',
  accent: '#3FE0C5',
  onAccent: '#032A24',
  accentText: '#5CEBD3',
  warn: '#FFC266',
  warnBg: 'rgba(255,194,102,0.15)',
  onWarn: '#2A1600',
  sheet: '#0B2234',
  dim: 'rgba(0,8,16,0.62)',
  glow: '#56C4EB',
};

export const light: Palette = {
  dark: false,
  bg: '#EEF5F7',
  surface: '#FFFFFF',
  surface2: '#E3EEF2',
  line: 'rgba(6,34,53,0.12)',
  text: '#062235',
  muted: '#3F5A68',
  accent: '#3FE0C5',
  onAccent: '#032A24',
  accentText: '#00745F',
  warn: '#8A4B00',
  warnBg: 'rgba(196,120,0,0.12)',
  onWarn: '#FFFFFF',
  sheet: '#FFFFFF',
  dim: 'rgba(4,21,38,0.38)',
  glow: '#56C4EB',
};

export const radius = Platform.select({ ios: { card: 24, chip: 22, button: 28 }, default: { card: 28, chip: 12, button: 18 } })!;
