// Shared building blocks: screen with the underwater light, surfaces (glass on iOS, tonal on Android), text,
// buttons that count taps during the timed test, chips, bottom sheet, QR and the simulated system dialogs.
import { BlurView } from 'expo-blur';
import * as Haptics from 'expo-haptics';
import qrcode from 'qrcode-generator';
import React, { useEffect, useMemo, useRef } from 'react';
import {
  Animated, Modal, Platform, Pressable, PressableProps, ScrollView, StyleProp, StyleSheet, Text, TextProps, TextStyle, View, ViewStyle,
} from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import Svg, { Defs, RadialGradient, Rect, Stop } from 'react-native-svg';
import { Icon, IconName } from './icons';
import { useApp } from './store';
import { radius } from './theme';

export const isIOS = Platform.OS === 'ios';

export function haptic(kind: 'light' | 'success' | 'warning' = 'light') {
  if (Platform.OS === 'web') return;
  if (kind === 'light') Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light).catch(() => undefined);
  else Haptics.notificationAsync(kind === 'success' ? Haptics.NotificationFeedbackType.Success : Haptics.NotificationFeedbackType.Warning).catch(() => undefined);
}

/** Light from the surface, at the top of every screen. */
export function Glow() {
  const { c } = useApp();
  return (
    <Svg style={StyleSheet.absoluteFill} width="100%" height={380} pointerEvents="none">
      <Defs>
        <RadialGradient id="g" cx="25%" cy="-10%" rx="110%" ry="85%">
          <Stop offset="0" stopColor={c.glow} stopOpacity={c.dark ? 0.3 : 0.2} />
          <Stop offset="1" stopColor={c.glow} stopOpacity={0} />
        </RadialGradient>
      </Defs>
      <Rect x="0" y="0" width="100%" height="380" fill="url(#g)" />
    </Svg>
  );
}

export function Screen({ children, scroll = true, bottom = 120, style }: { children: React.ReactNode; scroll?: boolean; bottom?: number; style?: StyleProp<ViewStyle> }) {
  const { c } = useApp();
  const insets = useSafeAreaInsets();
  const pad = { paddingTop: insets.top + 14, paddingHorizontal: 18, paddingBottom: bottom };
  return (
    <View style={{ flex: 1, backgroundColor: c.bg }}>
      <Glow />
      {scroll ? (
        <ScrollView contentContainerStyle={[pad, style]} showsVerticalScrollIndicator={false}>{children}</ScrollView>
      ) : (
        <View style={[{ flex: 1 }, pad, style]}>{children}</View>
      )}
    </View>
  );
}

type TxtKind = 'h1' | 'h2' | 'title' | 'body' | 'small' | 'label' | 'big';
const SIZES: Record<TxtKind, TextStyle> = {
  big: { fontSize: 30, fontWeight: '800', letterSpacing: -0.5 },
  h1: { fontSize: 28, fontWeight: '800', letterSpacing: -0.5 },
  h2: { fontSize: 22, fontWeight: '800', letterSpacing: -0.3 },
  title: { fontSize: 16, fontWeight: '800' },
  body: { fontSize: 15, lineHeight: 21 },
  small: { fontSize: 13, lineHeight: 18 },
  label: { fontSize: 11, fontWeight: '800', letterSpacing: 1.2 },
};
export function Txt({ kind = 'body', color, style, ...rest }: TextProps & { kind?: TxtKind; color?: 'text' | 'muted' | 'accent' | 'warn' | 'onAccent' | 'onWarn' }) {
  const { c } = useApp();
  const col = color === 'muted' ? c.muted : color === 'accent' ? c.accentText : color === 'warn' ? c.warn : color === 'onAccent' ? c.onAccent : color === 'onWarn' ? c.onWarn : c.text;
  return <Text {...rest} style={[SIZES[kind], { color: col }, style]} />;
}

/** A surface: blurred glass on iOS (Liquid Glass look), tonal surface on Android (Material 3). */
export function Card({ children, style, strong }: { children: React.ReactNode; style?: StyleProp<ViewStyle>; strong?: boolean }) {
  const { c } = useApp();
  const base: ViewStyle = { borderRadius: radius.card, overflow: 'hidden', borderWidth: isIOS ? StyleSheet.hairlineWidth : 0, borderColor: c.line };
  if (isIOS) {
    return (
      <View style={[base, style]}>
        <BlurView intensity={strong ? 60 : 35} tint={c.dark ? 'dark' : 'light'} style={StyleSheet.absoluteFill} />
        <View style={[StyleSheet.absoluteFill, { backgroundColor: c.surface }]} />
        {children}
      </View>
    );
  }
  return <View style={[base, { backgroundColor: strong ? c.surface2 : c.surface }, style]}>{children}</View>;
}

/** Pressable that counts as a tap during a timed test and gives an Android ripple. */
export function Press({ onPress, children, style, count = true, ...rest }: PressableProps & { count?: boolean; style?: StyleProp<ViewStyle>; children: React.ReactNode }) {
  const { tap, c } = useApp();
  return (
    <Pressable
      {...rest}
      android_ripple={{ color: c.dark ? 'rgba(255,255,255,0.12)' : 'rgba(6,34,53,0.08)' }}
      onPress={(e) => { if (count) tap(); onPress?.(e); }}
      style={({ pressed }) => [style as ViewStyle, isIOS && pressed ? { opacity: 0.7 } : null]}
    >
      {children}
    </Pressable>
  );
}

export function Chip({ label, on, onPress }: { label: string; on: boolean; onPress: () => void }) {
  const { c } = useApp();
  return (
    <Press accessibilityRole="button" accessibilityState={{ selected: on }} onPress={() => { haptic(); onPress(); }}
      style={{ height: 44, paddingHorizontal: 18, borderRadius: radius.chip, justifyContent: 'center', backgroundColor: on ? c.accent : c.surface, borderWidth: on || !isIOS ? 0 : StyleSheet.hairlineWidth, borderColor: c.line }}>
      <Text style={{ fontSize: 15, fontWeight: '800', color: on ? c.onAccent : c.text }}>{label}</Text>
    </Press>
  );
}

type BtnKind = 'primary' | 'secondary' | 'warn' | 'pay' | 'link';
export function Btn({ label, onPress, kind = 'primary', icon, disabled, style, count }: { label: string; onPress: () => void; kind?: BtnKind; icon?: IconName; disabled?: boolean; style?: StyleProp<ViewStyle>; count?: boolean }) {
  const { c } = useApp();
  const bg = kind === 'primary' ? c.accent : kind === 'warn' ? c.warn : kind === 'pay' ? (c.dark ? '#FFFFFF' : '#000000') : kind === 'secondary' ? c.surface2 : 'transparent';
  const fg = kind === 'primary' ? c.onAccent : kind === 'warn' ? c.onWarn : kind === 'pay' ? (c.dark ? '#000000' : '#FFFFFF') : kind === 'link' ? c.accentText : c.text;
  return (
    <Press accessibilityRole="button" accessibilityState={{ disabled }} disabled={disabled} onPress={onPress} count={count}
      style={[{ minHeight: kind === 'link' ? 44 : kind === 'pay' ? 58 : 52, borderRadius: kind === 'link' ? 8 : radius.button, backgroundColor: bg, flexDirection: 'row', alignItems: 'center', justifyContent: 'center', gap: 8, paddingHorizontal: kind === 'link' ? 6 : 18, opacity: disabled ? 0.45 : 1 }, style]}>
      {icon ? <Icon name={icon} size={19} color={fg} stroke={2} /> : null}
      <Text style={{ color: fg, fontSize: kind === 'pay' ? 18 : kind === 'link' ? 14 : 16, fontWeight: '800' }}>{label}</Text>
    </Press>
  );
}

export function Tag({ label, tone = 'plain', icon }: { label: string; tone?: 'plain' | 'warn' | 'ok'; icon?: IconName }) {
  const { c } = useApp();
  const bg = tone === 'warn' ? c.warnBg : c.surface2;
  const fg = tone === 'warn' ? c.warn : tone === 'ok' ? c.accentText : c.text;
  return (
    <View style={{ flexDirection: 'row', alignItems: 'center', gap: 4, paddingHorizontal: 8, paddingVertical: 3, borderRadius: 8, backgroundColor: bg, alignSelf: 'flex-start' }}>
      {icon ? <Icon name={icon} size={13} color={fg} stroke={2.4} /> : null}
      <Text style={{ fontSize: 12, fontWeight: '800', color: fg }}>{label}</Text>
    </View>
  );
}

export function Row({ children, style }: { children: React.ReactNode; style?: StyleProp<ViewStyle> }) {
  return <View style={[{ flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', gap: 12 }, style]}>{children}</View>;
}

export function IconButton({ icon, label, onPress }: { icon: IconName; label: string; onPress: () => void }) {
  const { c } = useApp();
  return (
    <Press accessibilityRole="button" accessibilityLabel={label} onPress={onPress}
      style={{ width: 44, height: 44, borderRadius: 22, alignItems: 'center', justifyContent: 'center', backgroundColor: c.surface }}>
      <Icon name={icon} color={c.text} />
    </Press>
  );
}

/** Bottom sheet over the current screen (not a new screen). */
export function Sheet({ visible, onClose, children, label }: { visible: boolean; onClose: () => void; children: React.ReactNode; label: string }) {
  const { c } = useApp();
  const insets = useSafeAreaInsets();
  const y = useRef(new Animated.Value(700)).current;
  useEffect(() => {
    if (visible) { y.setValue(700); Animated.spring(y, { toValue: 0, useNativeDriver: Platform.OS !== 'web', damping: 22, stiffness: 220, mass: 0.9 }).start(); }
  }, [visible, y]);
  return (
    <Modal visible={visible} transparent animationType="fade" onRequestClose={onClose} statusBarTranslucent>
      <View style={{ flex: 1, justifyContent: 'flex-end' }}>
        <Pressable accessibilityRole="button" accessibilityLabel={label + ': cerrar'} onPress={onClose} style={[StyleSheet.absoluteFill, { backgroundColor: c.dim }]} />
        <Animated.View accessibilityViewIsModal style={{ transform: [{ translateY: y }], maxHeight: '92%', backgroundColor: c.sheet, borderTopLeftRadius: isIOS ? 34 : 28, borderTopRightRadius: isIOS ? 34 : 28, paddingBottom: insets.bottom + 14 }}>
          <View style={{ width: 40, height: 5, borderRadius: 3, backgroundColor: c.line, alignSelf: 'center', marginTop: 10, marginBottom: 8 }} />
          <ScrollView contentContainerStyle={{ paddingHorizontal: 20, paddingBottom: 8 }} showsVerticalScrollIndicator={false}>{children}</ScrollView>
        </Animated.View>
      </View>
    </Modal>
  );
}

/** Imitation of a system dialog (sign in with Apple or Google, Apple Pay or Google Pay): only in this test version. */
export function SystemSheet({ visible, title, rows, footer, note }: { visible: boolean; title: string; rows: [string, string][]; footer: React.ReactNode; note?: string }) {
  const { c, t } = useApp();
  const insets = useSafeAreaInsets();
  const bg = c.dark ? (isIOS ? '#1C1C1E' : '#202124') : isIOS ? '#F2F2F7' : '#FFFFFF';
  const fg = c.dark ? '#FFFFFF' : '#000000';
  return (
    <Modal visible={visible} transparent animationType="slide" statusBarTranslucent>
      <View style={{ flex: 1, justifyContent: 'flex-end', backgroundColor: 'rgba(0,0,0,0.45)' }}>
        <View style={{ backgroundColor: bg, borderTopLeftRadius: 28, borderTopRightRadius: 28, padding: 20, paddingBottom: insets.bottom + 22 }}>
          <View style={{ flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', marginBottom: 8 }}>
            <Text style={{ color: fg, fontSize: 19, fontWeight: '800' }}>{title}</Text>
            <Text style={{ color: fg, opacity: 0.6, fontSize: 13 }}>{t('Simulado')}</Text>
          </View>
          {note ? <Text style={{ color: fg, opacity: 0.8, fontSize: 14, lineHeight: 20, marginBottom: 4 }}>{note}</Text> : null}
          {rows.map(([k, v], i) => (
            <View key={k} style={{ flexDirection: 'row', justifyContent: 'space-between', paddingVertical: 11, borderBottomWidth: i < rows.length - 1 ? StyleSheet.hairlineWidth : 0, borderColor: 'rgba(128,128,128,0.4)' }}>
              <Text style={{ color: fg, opacity: 0.7, fontSize: 15 }}>{k}</Text>
              <Text style={{ color: fg, fontSize: 15, fontWeight: i === rows.length - 1 ? '800' : '400' }}>{v}</Text>
            </View>
          ))}
          {footer}
        </View>
      </View>
    </Modal>
  );
}

export function QR({ value, size = 120 }: { value: string; size?: number }) {
  const cells = useMemo(() => {
    const q = qrcode(0, 'M');
    q.addData(value);
    q.make();
    const n = q.getModuleCount();
    const out: [number, number][] = [];
    for (let r = 0; r < n; r++) for (let col = 0; col < n; col++) if (q.isDark(r, col)) out.push([col, r]);
    return { n, out };
  }, [value]);
  const quiet = 2;
  const total = cells.n + quiet * 2;
  return (
    <Svg width={size} height={size} viewBox={`0 0 ${total} ${total}`} accessibilityLabel="QR">
      <Rect x="0" y="0" width={total} height={total} fill="#FFFFFF" rx="2" />
      {cells.out.map(([x, y]) => <Rect key={x + '-' + y} x={x + quiet} y={y + quiet} width="1.02" height="1.02" fill="#041526" />)}
    </Svg>
  );
}

/** Small banner shown while a timed test is running. */
export function TestBanner() {
  const { test, c, t } = useApp();
  const [, force] = React.useReducer((x: number) => x + 1, 0);
  useEffect(() => { if (!test) return; const id = setInterval(force, 200); return () => clearInterval(id); }, [test]);
  const insets = useSafeAreaInsets();
  if (!test) return null;
  const ms = Date.now() - test.start;
  const limit = test.kind === 'reserva' ? 30000 : 10000;
  return (
    <View pointerEvents="none" style={{ position: 'absolute', top: insets.top + 4, alignSelf: 'center', flexDirection: 'row', gap: 8, alignItems: 'center', paddingHorizontal: 12, paddingVertical: 6, borderRadius: 16, backgroundColor: ms < limit ? c.accent : c.warn }}>
      <Icon name="timer" size={16} color={ms < limit ? c.onAccent : c.onWarn} stroke={2.2} />
      <Text style={{ fontWeight: '800', fontVariant: ['tabular-nums'], color: ms < limit ? c.onAccent : c.onWarn }}>
        {(ms / 1000).toFixed(1)} s · {t('{n} toques', { n: test.taps })}
      </Text>
    </View>
  );
}
