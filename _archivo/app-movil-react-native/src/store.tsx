// State of the app: who is using it (diver, centre or freelance in this test version), language, theme, the
// diver's bookings and the timed tests. Saved on the phone (AsyncStorage) so it survives closing the app.
import AsyncStorage from '@react-native-async-storage/async-storage';
import React, { createContext, useCallback, useContext, useEffect, useMemo, useRef, useState } from 'react';
import { useColorScheme } from 'react-native';
import { Booking, initialBookings } from './demo';
import { deviceLang, Lang, translate } from './i18n';
import { dark, light, Palette } from './theme';

export type Role = 'buceador' | 'centro' | 'freelance';
export type ThemePref = 'sistema' | 'oscuro' | 'claro';
export type TestKind = 'reserva' | 'centro';
export type TestRun = { kind: TestKind; start: number; taps: number; firstTime: boolean };
export type TestResult = { kind: TestKind; ms: number; taps: number; firstTime: boolean; at: string };

type Saved = {
  role: Role | null; firstTime: boolean; lang: Lang | null; theme: ThemePref; bookings: Booking[]; results: TestResult[];
  blocked: number[]; offers: Record<string, 'ok' | 'no'>; checkins: Record<string, string>; cancelledSlots: string[];
};
const DEFAULTS: Saved = { role: null, firstTime: false, lang: null, theme: 'oscuro', bookings: initialBookings(), results: [], blocked: [4], offers: {}, checkins: {}, cancelledSlots: [] };
const KEY = 'worldives-app-0.1';

type Ctx = Saved & {
  ready: boolean; c: Palette; lang: Lang; t: (text: string, vars?: Record<string, string | number>) => string;
  set: (patch: Partial<Saved>) => void; reset: (role: Role | null, firstTime?: boolean) => void;
  test: TestRun | null; startTest: (kind: TestKind, firstTime?: boolean) => void; tap: () => void; finishTest: (kind: TestKind) => TestResult | null;
  addBooking: (b: Booking) => void; updateBooking: (code: string, patch: Partial<Booking>) => void;
};
const AppContext = createContext<Ctx | null>(null);

export function AppProvider({ children }: { children: React.ReactNode }) {
  const scheme = useColorScheme();
  const [saved, setSaved] = useState<Saved>(DEFAULTS);
  const [ready, setReady] = useState(false);
  const [test, setTest] = useState<TestRun | null>(null);
  const testRef = useRef<TestRun | null>(null);
  testRef.current = test;

  useEffect(() => {
    AsyncStorage.getItem(KEY).then((raw) => {
      if (raw) { try { setSaved({ ...DEFAULTS, ...JSON.parse(raw) }); } catch { /* a damaged copy: start again */ } }
      setReady(true);
    }, () => setReady(true));
  }, []);
  useEffect(() => { if (ready) AsyncStorage.setItem(KEY, JSON.stringify(saved)).catch(() => undefined); }, [saved, ready]);

  const set = useCallback((patch: Partial<Saved>) => setSaved((s) => ({ ...s, ...patch })), []);
  const lang: Lang = saved.lang ?? deviceLang();
  const isDark = saved.theme === 'oscuro' || (saved.theme === 'sistema' && scheme !== 'light');
  const t = useCallback((text: string, vars?: Record<string, string | number>) => translate(lang, text, vars), [lang]);

  const value = useMemo<Ctx>(() => ({
    ...saved, ready, lang, t, c: isDark ? dark : light, set, test,
    reset: (role, firstTime = false) => setSaved((s) => ({ ...DEFAULTS, lang: s.lang, theme: s.theme, results: s.results, role, firstTime,
      bookings: role === 'buceador' && firstTime ? [] : initialBookings() })),
    startTest: (kind, firstTime) => setTest({ kind, start: Date.now(), taps: 0, firstTime: firstTime ?? saved.firstTime }),
    tap: () => { if (testRef.current) setTest((x) => (x ? { ...x, taps: x.taps + 1 } : x)); },
    finishTest: (kind) => {
      const run = testRef.current;
      if (!run || run.kind !== kind) return null;
      const r: TestResult = { kind, ms: Date.now() - run.start, taps: run.taps, firstTime: run.firstTime, at: new Date().toISOString() };
      setTest(null);
      setSaved((s) => ({ ...s, results: [r, ...s.results].slice(0, 20) }));
      return r;
    },
    addBooking: (b) => setSaved((s) => ({ ...s, bookings: [b, ...s.bookings] })),
    updateBooking: (code, patch) => setSaved((s) => ({ ...s, bookings: s.bookings.map((b) => (b.code === code ? { ...b, ...patch } : b)) })),
  }), [saved, ready, lang, t, isDark, set, test]);

  return <AppContext.Provider value={value}>{children}</AppContext.Provider>;
}

export function useApp(): Ctx {
  const v = useContext(AppContext);
  if (!v) throw new Error('useApp fuera de AppProvider');
  return v;
}
