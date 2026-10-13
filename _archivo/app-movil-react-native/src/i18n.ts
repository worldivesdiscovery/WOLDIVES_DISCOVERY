// Texts of the app in Spanish (the source), English and French (decision of 13/10/2026). The Spanish text is the
// key, as in the web (public/idiomas/*.json). Another language on the phone → English.
import { getLocales } from 'expo-localization';
import en from './idiomas/en.json';
import fr from './idiomas/fr.json';

export type Lang = 'es' | 'en' | 'fr';
export const LANGS: { code: Lang; label: string }[] = [
  { code: 'es', label: 'Español' },
  { code: 'en', label: 'English' },
  { code: 'fr', label: 'Français' },
];
const PACKS: Record<Exclude<Lang, 'es'>, Record<string, string>> = { en, fr };

export function deviceLang(): Lang {
  const code = (getLocales()[0]?.languageCode || 'en').toLowerCase();
  return code === 'es' || code === 'fr' ? code : 'en';
}

export function translate(lang: Lang, text: string, vars?: Record<string, string | number>): string {
  let s = lang === 'es' ? text : PACKS[lang][text] ?? text;
  if (vars) for (const [k, v] of Object.entries(vars)) s = s.split('{' + k + '}').join(String(v));
  return s;
}

const DAYS: Record<Lang, string[]> = {
  es: ['domingo', 'lunes', 'martes', 'miércoles', 'jueves', 'viernes', 'sábado'],
  en: ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'],
  fr: ['dimanche', 'lundi', 'mardi', 'mercredi', 'jeudi', 'vendredi', 'samedi'],
};
const MONTHS: Record<Lang, string[]> = {
  es: ['ene', 'feb', 'mar', 'abr', 'may', 'jun', 'jul', 'ago', 'sep', 'oct', 'nov', 'dic'],
  en: ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'],
  fr: ['janv.', 'févr.', 'mars', 'avr.', 'mai', 'juin', 'juil.', 'août', 'sept.', 'oct.', 'nov.', 'déc.'],
};

export function weekday(lang: Lang, d: Date, short = false): string {
  const w = DAYS[lang][d.getDay()];
  return short ? w.slice(0, 3) : w;
}

/** «sáb 17 oct» / «Sat 17 Oct» / «sam. 17 oct.» */
export function shortDate(lang: Lang, d: Date): string {
  const w = weekday(lang, d, true) + (lang === 'fr' ? '.' : '');
  return lang === 'en' ? `${w} ${d.getDate()} ${MONTHS.en[d.getMonth()]}` : `${w} ${d.getDate()} ${MONTHS[lang][d.getMonth()]}`;
}

export function money(lang: Lang, n: number): string {
  const v = Number.isInteger(n) ? String(n) : n.toFixed(2).replace('.', lang === 'en' ? '.' : ',');
  return lang === 'en' ? '€' + v : v + ' €';
}

export function seconds(lang: Lang, ms: number): string {
  const v = (ms / 1000).toFixed(1);
  return (lang === 'en' ? v : v.replace('.', ',')) + ' s';
}
