// Sample data of version 0.1 (the same fictitious centre as the web's test environment). In version 0.2 these
// functions are replaced by calls to /api/v1/ of the server: the screens do not change.
export type Img = 'arrecife' | 'buceadores' | 'corales';
export type Slot = {
  id: string; day: number; time: string; dur: string; service: string; title: string; point: string; meet: string;
  level: string; rank: number; spots: number; price: number; wave: number; wind: number; img: Img; live?: boolean;
};
export type Diver = { name: string; level: string; dives: number; suit: string; boot: string; bcd: string; fins: string; paid: boolean; missing: '' | 'descargo' | 'seguro'; rent: boolean; code?: string };
export type CentreSlot = { id: string; time: string; title: string; where: string; cap: number; staff: string; tanks: number; divers: Diver[] };

export const CENTRE = {
  name: 'Centro de Buceo Pruebas',
  phone: '+34600000101',
  phoneText: '600 000 101',
  whatsapp: '34600000101',
  meet: 'Puerto de Xàbia, pantalán 3',
  maps: 'https://maps.google.com/?q=Puerto+de+X%C3%A0bia',
  policy: { freeHours: 48, refundPct: 50 },
};

export const MY_RANK = 2; // Bea: Advanced Open Water
export const RENT_PRICE = 15;

const SERVICES = {
  simple: { title: 'Inmersión simple en barco', dur: '3 h', level: 'Open Water', rank: 1, price: 45, img: 'arrecife' as Img },
  doble: { title: 'Doble inmersión en barco', dur: '4 h', level: 'Advanced', rank: 2, price: 80, img: 'buceadores' as Img },
  bautizo: { title: 'Bautizo de buceo', dur: '2 h 30', level: 'Sin titulación', rank: 0, price: 65, img: 'corales' as Img },
  nocturna: { title: 'Nocturna desde costa', dur: '1 h 30', level: 'Advanced', rank: 2, price: 50, img: 'corales' as Img },
  profunda: { title: 'Inmersión profunda', dur: '3 h', level: 'Rescue + profunda', rank: 3, price: 60, img: 'buceadores' as Img },
};
type ServiceKey = keyof typeof SERVICES;

// What leaves each day (offset 0 = today: only the afternoon is still open).
const PLAN: [string, ServiceKey, string, string][][] = [
  [['08:30', 'profunda', 'Cap Prim', CENTRE.meet], ['09:00', 'simple', 'Cabo de San Antonio', CENTRE.meet], ['11:30', 'doble', 'Cabo Negro', CENTRE.meet], ['16:00', 'bautizo', 'Cala Granadella', 'Centro de Buceo Pruebas']],
  [['09:00', 'doble', 'Isla del Portitxol', CENTRE.meet], ['10:00', 'bautizo', 'Cala Granadella', 'Centro de Buceo Pruebas'], ['15:30', 'simple', 'Cabo de San Antonio', CENTRE.meet]],
  [['09:00', 'simple', 'Isla del Portitxol', CENTRE.meet], ['11:30', 'profunda', 'Cap Prim', CENTRE.meet], ['20:30', 'nocturna', 'Cala Granadella', 'Aparcamiento de la Granadella']],
];
const TODAY: [string, ServiceKey, string, string][] = [['15:30', 'simple', 'Isla del Portitxol', CENTRE.meet], ['20:30', 'nocturna', 'Cala Granadella', 'Aparcamiento de la Granadella']];

function seed(s: string): number { let h = 7; for (const c of s) h = (h * 31 + c.charCodeAt(0)) % 9973; return h; }

export function dayDate(offset: number): Date {
  const d = new Date();
  d.setHours(12, 0, 0, 0);
  d.setDate(d.getDate() + offset);
  return d;
}

export function slotsFor(offset: number): Slot[] {
  const plan = offset === 0 ? TODAY : PLAN[offset % PLAN.length];
  return plan.map(([time, key, point, meet], i) => {
    const s = SERVICES[key];
    const h = seed(offset + time + point);
    return {
      id: `d${offset}-${i}`, day: offset, time, dur: s.dur, service: key, title: s.title, point, meet, level: s.level, rank: s.rank,
      spots: 2 + (h % 7), price: s.price, wave: Math.round((2 + (h % 7)) * 10) / 100 + 0.2, wind: 6 + (h % 12), img: s.img,
      live: offset === 1 && i === 1,
    };
  });
}

/** Next date (offset ≥ from) on which the same service leaves from the same point: «Repetir». */
export function nextSame(service: string, point: string, from = 1): Slot | undefined {
  for (let d = from; d < from + 21; d++) {
    const s = slotsFor(d).find((x) => x.service === service && x.point === point);
    if (s) return s;
  }
  return undefined;
}

export function findSlot(id: string): Slot | undefined {
  const day = Number(id.slice(1).split('-')[0]);
  return slotsFor(day).find((s) => s.id === id);
}

/** The «finde» chip: the next Saturday (or Sunday when today is Saturday). */
export function weekendOffset(): number {
  const dow = new Date().getDay();
  if (dow === 6) return 1;
  if (dow === 0) return 6;
  return 6 - dow;
}

// ---- the diver's own data (account mode)
export const PROFILE = {
  name: 'Bea Buzo', initials: 'BB', cert: 'Advanced Open Water · PADI', dives: 64, maxDepth: 31, sites: 12,
  sizes: { suit: 'M', boot: '42', bcd: 'M', fins: '42-43' }, insurance: '05/2027',
};
export type Booking = {
  code: string; slotId: string; service: string; title: string; point: string; meet: string; day: number; time: string;
  people: number; equip: boolean; paid: 'full' | 'deposit' | 'center'; amount: number; waiver: boolean; cancelled?: boolean; refund?: number;
};
export function initialBookings(): Booking[] {
  return [
    { code: 'WOD-000124', slotId: 'd0-0', service: 'simple', title: SERVICES.simple.title, point: 'Isla del Portitxol', meet: CENTRE.meet, day: 0, time: '15:30', people: 1, equip: true, paid: 'full', amount: 60, waiver: false },
    { code: 'WOD-000117', slotId: 'd4-x', service: 'doble', title: SERVICES.doble.title, point: 'Cabo Negro', meet: CENTRE.meet, day: 4, time: '08:30', people: 1, equip: true, paid: 'deposit', amount: 24, waiver: true },
  ];
}
export const HISTORY = [
  { day: -15, title: SERVICES.simple.title, service: 'simple', point: 'Isla del Portitxol', depth: 18, minutes: 46 },
  { day: -29, title: SERVICES.simple.title, service: 'simple', point: 'Cabo de San Antonio', depth: 22, minutes: 41 },
];

export const POINTS = [
  { name: 'Cabo de San Antonio', type: 'Barco', depth: 24, level: 'Open Water', rank: 1, note: 'Reserva marina. Paredes y praderas de posidonia.' },
  { name: 'Isla del Portitxol', type: 'Barco', depth: 18, level: 'Open Water', rank: 1, note: 'Rodea la isla: meros, pulpos y nudibranquios.' },
  { name: 'Cabo Negro', type: 'Barco', depth: 30, level: 'Advanced', rank: 2, note: 'Bajos rocosos con corriente moderada.' },
  { name: 'Cala Granadella', type: 'Costa', depth: 12, level: 'Sin titulación', rank: 0, note: 'Entrada desde la playa. Ideal para bautizos y nocturnas.' },
  { name: 'Cap Prim', type: 'Barco', depth: 38, level: 'Rescue + profunda', rank: 3, note: 'Pared que cae a más de 35 m.' },
  { name: 'Cala Granadella de noche', type: 'Nocturna', depth: 12, level: 'Advanced', rank: 2, note: 'Pulpos, sepias y morenas activas.' },
];

// ---- the centre
const D = (name: string, level: string, dives: number, suit: string, boot: string, bcd: string, fins: string, paid: boolean, missing: Diver['missing'], rent: boolean, code?: string): Diver =>
  ({ name, level, dives, suit, boot, bcd, fins, paid, missing, rent, code });
export const CENTRE_DAYS: Record<'hoy' | 'manana', { income: number; slots: CentreSlot[] }> = {
  hoy: { income: 1240, slots: [
    { id: 'c0', time: '09:00', title: 'Doble inmersión en barco', where: 'Cabo Negro · barco Neptuno', cap: 12, staff: 'Iván (instructor) · Tito (freelance)', tanks: 2, divers: [
      D('Marta R.', 'Open Water', 12, 'S', '38', 'S', '38-39', true, 'descargo', true, 'WOD-000101'), D('Jonas K.', 'Rescue', 140, 'L', '44', 'L', '44-45', true, '', false, 'WOD-000102'),
      D('Lucía P.', 'Advanced', 31, 'S', '38', 'S', '38-39', false, '', true, 'WOD-000103'), D('Pierre D.', 'Advanced', 55, 'M', '42', 'M', '42-43', true, 'descargo', true, 'WOD-000104'),
      D('Sven A.', 'Divemaster', 300, 'XL', '45', 'L', '44-45', true, '', false, 'WOD-000105'), D('Ana M.', 'Open Water', 9, 'M', '40', 'M', '40-41', true, '', true, 'WOD-000106'),
      D('Tom H.', 'Advanced', 48, 'L', '43', 'L', '42-43', true, '', true, 'WOD-000107'), D('Giulia F.', 'Open Water', 15, 'S', '37', 'S', '36-37', true, '', true, 'WOD-000108'),
      D('Erik L.', 'Advanced', 70, 'L', '44', 'L', '44-45', true, '', true, 'WOD-000109')] },
    { id: 'c1', time: '15:30', title: 'Inmersión simple en barco', where: 'Isla del Portitxol · barco Neptuno', cap: 10, staff: 'Iván (instructor)', tanks: 1, divers: [
      D('Bea B.', 'Advanced', 64, 'M', '42', 'M', '42-43', true, 'descargo', true, 'WOD-000124'), D('Nuria S.', 'Open Water', 6, 'S', '38', 'S', '38-39', true, '', true, 'WOD-000120'),
      D('Paul W.', 'Open Water', 20, 'M', '42', 'M', '42-43', true, '', true, 'WOD-000121'), D('Chen L.', 'Advanced', 40, 'M', '41', 'M', '40-41', true, '', true, 'WOD-000122'),
      D('Iker G.', 'Rescue', 90, 'L', '43', 'L', '42-43', true, '', false, 'WOD-000123'), D('Sara V.', 'Open Water', 11, 'S', '37', 'S', '36-37', true, '', true, 'WOD-000125'),
      D('Mia T.', 'Advanced', 28, 'M', '39', 'M', '38-39', true, '', true, 'WOD-000126')] },
    { id: 'c2', time: '20:30', title: 'Nocturna desde costa', where: 'Cala Granadella · desde la orilla', cap: 6, staff: 'Tito (freelance)', tanks: 1, divers: [
      D('Jonas K.', 'Rescue', 140, 'L', '44', 'L', '44-45', true, '', false), D('Tom H.', 'Advanced', 48, 'L', '43', 'L', '42-43', true, 'descargo', true),
      D('Chen L.', 'Advanced', 40, 'M', '41', 'M', '40-41', true, '', true), D('Mia T.', 'Advanced', 28, 'M', '39', 'M', '38-39', true, '', true)] },
  ] },
  manana: { income: 980, slots: [
    { id: 'c3', time: '08:30', title: 'Inmersión profunda', where: 'Cap Prim · barco Neptuno', cap: 6, staff: 'Iván (instructor)', tanks: 1, divers: [
      D('Sven A.', 'Divemaster', 300, 'XL', '45', 'L', '44-45', true, '', false), D('Jonas K.', 'Rescue', 140, 'L', '44', 'L', '44-45', true, '', false),
      D('Iker G.', 'Rescue', 90, 'L', '43', 'L', '42-43', true, 'seguro', true)] },
    { id: 'c4', time: '11:30', title: 'Doble inmersión en barco', where: 'Cabo Negro · barco Neptuno', cap: 12, staff: 'Iván (instructor) · Tito (freelance)', tanks: 2, divers: [
      D('Bea B.', 'Advanced', 64, 'M', '42', 'M', '42-43', true, '', true), D('Lucía P.', 'Advanced', 31, 'S', '38', 'S', '38-39', true, 'descargo', true),
      D('Erik L.', 'Advanced', 70, 'L', '44', 'L', '44-45', true, '', true), D('Paul W.', 'Open Water', 20, 'M', '42', 'M', '42-43', false, '', true),
      D('Ana M.', 'Open Water', 9, 'M', '40', 'M', '40-41', true, 'descargo', true), D('Chen L.', 'Advanced', 40, 'M', '41', 'M', '40-41', true, '', true),
      D('Sara V.', 'Open Water', 11, 'S', '37', 'S', '36-37', true, '', true), D('Mia T.', 'Advanced', 28, 'M', '39', 'M', '38-39', true, '', true)] },
    { id: 'c5', time: '16:00', title: 'Bautizo de buceo', where: 'Cala Granadella · desde la orilla', cap: 5, staff: 'Tito (freelance)', tanks: 1, divers: [
      D('Hugo B.', 'Sin titulación', 0, 'M', '42', 'M', '42-43', true, 'descargo', true), D('Clara B.', 'Sin titulación', 0, 'S', '37', 'S', '36-37', true, '', true),
      D('Leo N.', 'Sin titulación', 0, 'L', '44', 'L', '44-45', false, '', true)] },
  ] },
};
export const CLIENTS = [
  { name: 'Bea Buzo', level: 'Advanced', dives: 64, last: -15, phone: '+34611000102' },
  { name: 'Jonas Kraus', level: 'Rescue', dives: 140, last: -2, phone: '+4915100000000' },
  { name: 'Lucía Pérez', level: 'Advanced', dives: 31, last: -9, phone: '+34611000103' },
  { name: 'Pierre Dubois', level: 'Advanced', dives: 55, last: -30, phone: '+33600000000' },
  { name: 'Sven Andersen', level: 'Divemaster', dives: 300, last: -1, phone: '+4670000000' },
];

// ---- the freelance
export const FREELANCE = {
  name: 'Tito', role: 'Guía e instructor',
  today: [
    { time: '09:00', what: 'Guía · Doble inmersión en barco', where: 'Centro de Buceo Pruebas · ' + CENTRE.meet, who: '9 buceadores · tu grupo: 4 · Open Water y Advanced', direct: false },
    { time: '20:30', what: 'Nocturna desde costa · Cala Granadella', where: 'Aparcamiento de la Granadella', who: '4 buceadores', direct: true },
  ],
  busy: [0, 1],
  pending: 240,
  offers: [
    { id: 'o1', day: 2, time: '09:00', fee: 70, what: 'Guía · Doble inmersión en barco', where: 'Centro de Buceo Pruebas · Isla del Portitxol · 8 buceadores' },
    { id: 'o2', day: 3, time: '10:00', fee: 90, what: 'Instructor · Curso Open Water, día 2', where: 'Centro de Buceo Pruebas · Cala Granadella · 4 alumnos' },
  ],
  payments: [
    { day: -3, what: 'Guía · Doble inmersión (Centro de Buceo Pruebas)', amount: 70, paid: true },
    { day: -2, what: 'Nocturna · reserva directa (4 buceadores)', amount: 200, paid: true },
    { day: 0, what: 'Guía · Doble inmersión (Centro de Buceo Pruebas)', amount: 70, paid: false },
    { day: 0, what: 'Nocturna · reserva directa (4 buceadores)', amount: 170, paid: false },
  ],
  documents: [
    { name: 'Instructor PADI (OWSI)', until: '2027-12-31', days: 400 },
    { name: 'Seguro de responsabilidad civil', until: '', days: 32 },
    { name: 'Primeros auxilios (EFR)', until: '', days: 120 },
  ],
};
