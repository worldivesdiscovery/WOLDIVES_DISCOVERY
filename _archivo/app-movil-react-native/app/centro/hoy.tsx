// «Hoy» is the centre's home: the whole day in 1 tap, and who dives tomorrow with the equipment to prepare in 1–2.
// Cancel for weather: the v50.47 notices (push, WhatsApp from the centre's number, email), 10 s to undo.
import { router } from 'expo-router';
import React, { useEffect, useMemo, useState } from 'react';
import { TextInput, View } from 'react-native';
import { CENTRE_DAYS, CentreSlot, dayDate, Diver } from '@/demo';
import { Icon } from '@/icons';
import { money, seconds, shortDate } from '@/i18n';
import { TestResult, useApp } from '@/store';
import { Btn, Card, Chip, haptic, Press, Row, Screen, Sheet, Tag, Txt } from '@/ui';

type DayKey = 'hoy' | 'manana';
const REASONS = ['Mal tiempo', 'Estado del mar', 'Avería del barco', 'Otro'];

export default function CentroHoy() {
  const { t, c, lang, checkins, cancelledSlots, set, finishTest } = useApp();
  const [day, setDay] = useState<DayKey>('hoy');
  const [open, setOpen] = useState<string | null>(null);
  const [equip, setEquip] = useState<DayKey | null>(null);
  const [result, setResult] = useState<TestResult | null>(null);
  const [meteo, setMeteo] = useState<CentreSlot | null>(null);
  const [undo, setUndo] = useState<{ id: string; until: number; n: number } | null>(null);
  const [, tick] = useState(0);
  const data = CENTRE_DAYS[day];

  useEffect(() => {
    if (!undo) return;
    const id = setInterval(() => {
      tick((x) => x + 1);
      if (Date.now() >= undo.until) { set({ cancelledSlots: [...cancelledSlots, undo.id] }); haptic('success'); setUndo(null); }
    }, 250);
    return () => clearInterval(id);
  }, [undo, cancelledSlots, set]);

  function openEquip(k: DayKey) {
    setEquip(k);
    if (k === 'manana') { const r = finishTest('centro'); if (r) { setResult(r); haptic('success'); } }
  }
  const alerts = (s: CentreSlot) => {
    const w = s.divers.filter((d) => d.missing === 'descargo').length, ins = s.divers.filter((d) => d.missing === 'seguro').length, unpaid = s.divers.filter((d) => !d.paid).length;
    return [w ? t('{n} sin descargo', { n: w }) : '', ins ? t('{n} sin seguro', { n: ins }) : '', unpaid ? t('{n} sin pagar', { n: unpaid }) : ''].filter(Boolean);
  };
  const tomorrow = CENTRE_DAYS.manana.slots;
  const tomorrowDivers = tomorrow.reduce((n, s) => n + s.divers.length, 0);

  return (
    <Screen bottom={190}>
      <Row>
        <View>
          <Txt kind="small" color="muted" style={{ fontWeight: '700' }}>Centro de Buceo Pruebas</Txt>
          <Txt kind="h1">{(day === 'hoy' ? t('Hoy') : t('Mañana')) + ' · ' + shortDate(lang, dayDate(day === 'hoy' ? 0 : 1))}</Txt>
        </View>
      </Row>
      <View style={{ flexDirection: 'row', gap: 8, marginVertical: 12 }}>
        <Chip label={t('Hoy')} on={day === 'hoy'} onPress={() => { setDay('hoy'); setOpen(null); }} />
        <Chip label={t('Mañana')} on={day === 'manana'} onPress={() => { setDay('manana'); setOpen(null); }} />
      </View>
      <View style={{ flexDirection: 'row', gap: 8, marginBottom: 12 }}>
        {[[day === 'hoy' ? t('HOY') : t('MAÑANA'), money(lang, data.income)], [t('SEMANA'), money(lang, 6380)], [t('NUEVAS'), '5']].map(([l, v]) => (
          <Card key={l} style={{ flex: 1, padding: 12 }}><Txt kind="label" color="muted" numberOfLines={1} adjustsFontSizeToFit style={{ letterSpacing: 0.4 }}>{l}</Txt><Txt kind="h2" style={{ fontSize: 19 }}>{v}</Txt></Card>
        ))}
      </View>

      {undo ? (
        <Card strong style={{ padding: 14, marginBottom: 10, flexDirection: 'row', alignItems: 'center', gap: 10 }}>
          <Txt kind="small" style={{ flex: 1, fontWeight: '700' }}>{t('Avisando a {n} buceadores en {s} s', { n: undo.n, s: Math.max(0, Math.ceil((undo.until - Date.now()) / 1000)) })}</Txt>
          <Btn kind="warn" label={t('Deshacer')} onPress={() => setUndo(null)} style={{ minHeight: 44 }} />
        </Card>
      ) : null}

      <View style={{ gap: 8 }}>
        {data.slots.map((s) => {
          const n = s.divers.length;
          const a = alerts(s);
          const cancelled = cancelledSlots.includes(s.id);
          const isOpen = open === s.id;
          return (
            <Card key={s.id} style={{ opacity: cancelled ? 0.6 : 1 }}>
              <Press accessibilityRole="button" accessibilityState={{ expanded: isOpen }} onPress={() => setOpen(isOpen ? null : s.id)} style={{ padding: 14 }}>
                <Row><Txt kind="h2">{s.time}</Txt><Txt kind="title">{n}/{s.cap}</Txt></Row>
                <Txt kind="title" style={{ marginTop: 2 }}>{t(s.title)}</Txt>
                <Txt kind="small" color="muted">{s.where}</Txt>
                <View style={{ height: 6, borderRadius: 3, backgroundColor: c.surface2, marginTop: 8, overflow: 'hidden' }}>
                  <View style={{ width: `${Math.round((100 * n) / s.cap)}%`, height: 6, backgroundColor: c.accent, borderRadius: 3 }} />
                </View>
                <Txt kind="small" color="muted" style={{ marginTop: 6 }}>{s.staff}</Txt>
                <View style={{ flexDirection: 'row', flexWrap: 'wrap', gap: 6, marginTop: 8 }}>
                  {cancelled ? <Tag tone="warn" icon="alert" label={t('Cancelada · avisados {n}', { n })} /> : a.length ? a.map((x) => <Tag key={x} tone="warn" icon="alert" label={x} />) : <Tag tone="ok" label={t('Todo listo')} />}
                </View>
              </Press>
              {isOpen ? (
                <View style={{ paddingHorizontal: 14, paddingBottom: 12 }}>
                  {s.divers.map((d) => <DiverRow key={d.name} d={d} checked={!!(d.code && checkins[d.code])} />)}
                  {!cancelled && day === 'hoy' ? (
                    <View style={{ flexDirection: 'row', gap: 8, marginTop: 10 }}>
                      <Btn kind="secondary" icon="scan" label={t('Check-in')} onPress={() => router.push({ pathname: '/checkin', params: { slot: s.id } })} style={{ flex: 1 }} />
                      <Btn kind="warn" label={t('Cancelar por meteo')} onPress={() => setMeteo(s)} style={{ flex: 1 }} />
                    </View>
                  ) : !cancelled ? <Btn kind="warn" label={t('Cancelar por meteo')} onPress={() => setMeteo(s)} style={{ marginTop: 10 }} /> : null}
                </View>
              ) : null}
            </Card>
          );
        })}
      </View>

      {day === 'hoy' ? (
        <Press accessibilityRole="button" onPress={() => openEquip('manana')} style={{ marginTop: 12 }}>
          <Card style={{ padding: 14, flexDirection: 'row', alignItems: 'center', gap: 12 }}>
            <View style={{ flex: 1 }}>
              <Txt kind="label" color="accent">{t('MAÑANA') + ' · ' + shortDate(lang, dayDate(1)).toUpperCase()}</Txt>
              <Txt kind="title" style={{ marginTop: 2 }}>{t('{s} salidas · {n} buceadores', { s: tomorrow.length, n: tomorrowDivers })}</Txt>
              <Txt kind="small" color="muted">{t('Ver quién va y el equipo a preparar')}</Txt>
            </View>
            <Icon name="chevron" color={c.muted} />
          </Card>
        </Press>
      ) : (
        <Btn kind="secondary" label={t('Equipo a preparar · mañana')} onPress={() => openEquip('manana')} style={{ marginTop: 12 }} />
      )}

      <Btn icon="scan" label={t('Escanear QR')} onPress={() => router.push('/checkin')} style={{ marginTop: 14 }} />

      <EquipSheet day={equip} result={result} onClose={() => { setEquip(null); setResult(null); }} />
      <MeteoSheet slot={meteo} onClose={() => setMeteo(null)} onSend={(s) => { setMeteo(null); setUndo({ id: s.id, until: Date.now() + 10000, n: s.divers.length }); }} />
    </Screen>
  );
}

function DiverRow({ d, checked }: { d: Diver; checked: boolean }) {
  const { t, c } = useApp();
  return (
    <View style={{ paddingVertical: 9, borderTopWidth: 1, borderColor: c.line, gap: 2 }}>
      <Row>
        <Txt kind="small" style={{ fontWeight: '800', flex: 1 }}>{d.name} <Txt kind="small" color="muted">· {t(d.level)} · {t('{n} inm.', { n: d.dives })}</Txt></Txt>
        <Txt kind="small" color={d.paid ? 'accent' : 'warn'} style={{ fontWeight: '800' }}>{d.paid ? t('Pagado') : t('Sin pagar')}</Txt>
      </Row>
      <Row>
        <Txt kind="small" color="muted">{d.rent ? t('Traje {s} · escarpín {b} · chaleco {c}', { s: d.suit, b: d.boot, c: d.bcd }) : t('Equipo propio')}</Txt>
        <Txt kind="small" color={d.missing ? 'warn' : checked ? 'accent' : 'muted'} style={{ fontWeight: '700' }}>
          {d.missing ? t('Falta {x}', { x: t(d.missing) }) : checked ? t('Dentro') : t('Documentos listos')}
        </Txt>
      </Row>
    </View>
  );
}

function count(ds: Diver[], key: 'suit' | 'boot' | 'bcd' | 'fins'): string {
  const m: Record<string, number> = {};
  ds.forEach((d) => { m[d[key]] = (m[d[key]] || 0) + 1; });
  return Object.keys(m).sort((a, b) => a.localeCompare(b, 'es', { numeric: true })).map((k) => `${k}: ${m[k]}`).join(' · ');
}

function EquipSheet({ day, result, onClose }: { day: DayKey | null; result: TestResult | null; onClose: () => void }) {
  const { t, lang, c } = useApp();
  const slots = day ? CENTRE_DAYS[day].slots : [];
  const all = slots.flatMap((s) => s.divers);
  const rent = all.filter((d) => d.rent);
  const tanks = slots.reduce((n, s) => n + s.divers.length * s.tanks, 0);
  const ok = result ? result.ms < 10000 : false;
  return (
    <Sheet visible={!!day} onClose={onClose} label={t('Equipo a preparar')}>
      {result ? (
        <Card strong style={{ padding: 12, marginBottom: 12, flexDirection: 'row', gap: 10, alignItems: 'center' }}>
          <Icon name="timer" size={24} color={ok ? c.accentText : c.warn} />
          <Txt kind="small" color={ok ? 'accent' : 'warn'} style={{ flex: 1, fontWeight: '800' }}>
            {t('{s} y {n} toques', { s: seconds(lang, result.ms), n: result.taps })} · {ok ? t('dentro del objetivo (10 s)') : t('fuera del objetivo (10 s)')}
          </Txt>
        </Card>
      ) : null}
      <Txt kind="h2">{t('Equipo para mañana') + ', ' + shortDate(lang, dayDate(1))}</Txt>
      <Txt kind="small" color="muted" style={{ marginTop: 4, marginBottom: 12 }}>{t('{s} salidas · {n} buceadores · {r} alquilan equipo', { s: slots.length, n: all.length, r: rent.length })}</Txt>
      <View style={{ flexDirection: 'row', flexWrap: 'wrap', gap: 8 }}>
        {[[t('Trajes'), count(rent, 'suit')], [t('Escarpines'), count(rent, 'boot')], [t('Chalecos'), count(rent, 'bcd')], [t('Aletas'), count(rent, 'fins')], [t('Botellas'), t('{n} de 12 L (una por inmersión)', { n: tanks })], [t('Lastre'), t('Según la ficha de cada uno')]].map(([l, v]) => (
          <View key={l} style={{ width: '48%', padding: 10, borderRadius: 14, backgroundColor: c.surface2 }}>
            <Txt kind="small" style={{ fontWeight: '800' }}>{l}</Txt>
            <Txt kind="small" color="muted">{v}</Txt>
          </View>
        ))}
      </View>
      <Txt kind="label" color="muted" style={{ marginTop: 16, marginBottom: 4 }}>{t('QUIÉN VA')}</Txt>
      {slots.map((s) => (
        <View key={s.id} style={{ paddingVertical: 10, borderTopWidth: 1, borderColor: c.line }}>
          <Txt kind="small" style={{ fontWeight: '800' }}>{s.time} · {t(s.title)} · {t('{n} buceadores', { n: s.divers.length })}</Txt>
          <Txt kind="small" color="muted">{s.divers.map((d) => d.name).join(', ')}</Txt>
        </View>
      ))}
    </Sheet>
  );
}

function MeteoSheet({ slot, onClose, onSend }: { slot: CentreSlot | null; onClose: () => void; onSend: (s: CentreSlot) => void }) {
  const { t, c, lang } = useApp();
  const [reason, setReason] = useState(REASONS[0]);
  const [refund, setRefund] = useState(false);
  const [typed, setTyped] = useState('');
  const dateHint = useMemo(() => { const d = dayDate(slot && CENTRE_DAYS.manana.slots.includes(slot) ? 1 : 0); return `${String(d.getDate()).padStart(2, '0')}/${String(d.getMonth() + 1).padStart(2, '0')}`; }, [slot]);
  useEffect(() => { setTyped(''); setRefund(false); setReason(REASONS[0]); }, [slot]);
  if (!slot) return <Sheet visible={false} onClose={onClose} label=""><View /></Sheet>;
  const n = slot.divers.length;
  const paid = slot.divers.filter((d) => d.paid).length;
  const offset = CENTRE_DAYS.manana.slots.includes(slot) ? 1 : 0;
  return (
    <Sheet visible onClose={onClose} label={t('Cancelar salida y avisar a todos')}>
      <Txt kind="h2">{t('Cancelar salida y avisar a todos')}</Txt>
      <Txt kind="small" color="muted" style={{ marginTop: 2 }}>{slot.time} · {t(slot.title)} · {t('{n} buceadores', { n })}</Txt>
      <View style={{ flexDirection: 'row', flexWrap: 'wrap', gap: 8, marginTop: 12 }}>
        {REASONS.map((r) => <Chip key={r} label={t(r)} on={reason === r} onPress={() => setReason(r)} />)}
      </View>
      <View style={{ gap: 6, marginTop: 12 }}>
        {[[false, 'Cada uno elige', 'otra fecha o la devolución íntegra'], [true, 'Devolver ya a todos', 'desde tu cuenta de Stripe']].map(([v, a, b]) => (
          <Press key={String(v)} accessibilityRole="radio" accessibilityState={{ checked: refund === v }} onPress={() => setRefund(Boolean(v))}
            style={{ flexDirection: 'row', gap: 10, alignItems: 'center', padding: 12, borderRadius: 16, backgroundColor: c.surface2, borderWidth: 1.5, borderColor: refund === v ? c.accent : 'transparent' }}>
            <View style={{ width: 20, height: 20, borderRadius: 10, borderWidth: refund === v ? 6 : 2, borderColor: refund === v ? c.accent : c.muted }} />
            <Txt kind="small" style={{ flex: 1 }}><Txt kind="small" style={{ fontWeight: '800' }}>{t(String(a))}</Txt> <Txt kind="small" color="muted">{t(String(b))}</Txt></Txt>
          </Press>
        ))}
      </View>
      <View style={{ flexDirection: 'row', gap: 6, marginTop: 12 }}>
        {[['Push', n], ['WhatsApp', Math.max(0, n - 1)], [t('Correo'), n]].map(([l, v]) => (
          <View key={String(l)} style={{ flex: 1, alignItems: 'center', padding: 8, borderRadius: 14, backgroundColor: c.surface2 }}>
            <Txt kind="h2" style={{ fontSize: 18 }}>{v}</Txt><Txt kind="small" style={{ fontWeight: '700' }}>{l}</Txt>
          </View>
        ))}
      </View>
      <Txt kind="small" color="muted" style={{ marginTop: 8 }}>{slot.divers.map((d) => d.name).join(', ')}{refund ? ' · ' + t('{n} han pagado', { n: paid }) : ''}</Txt>
      <View style={{ marginTop: 10, padding: 12, borderRadius: 16, borderBottomLeftRadius: 4, backgroundColor: '#DCF8C6' }}>
        <Txt kind="small" style={{ color: '#0B1F14' }}>{t('Hola. {c} ha cancelado tu salida del {d} a las {h}. Motivo: {r}. {m}', { c: 'Centro de Buceo Pruebas', d: shortDate(lang, dayDate(offset)), h: slot.time, r: t(reason).toLowerCase(), m: refund ? t('Te devolvemos el importe en tu tarjeta.') : t('Elige otra fecha o la devolución íntegra con el botón.') })}</Txt>
      </View>
      <Txt kind="small" style={{ fontWeight: '700', marginTop: 12 }}>{t('Para confirmar, escribe la fecha de la salida ({d})', { d: dateHint })}</Txt>
      <TextInput value={typed} onChangeText={setTyped} placeholder={dateHint} placeholderTextColor={c.muted} keyboardType="numbers-and-punctuation" accessibilityLabel={t('Fecha de la salida')}
        style={{ marginTop: 6, height: 48, borderRadius: 14, paddingHorizontal: 12, backgroundColor: c.surface2, color: c.text, fontSize: 16, fontWeight: '700' }} />
      <Btn kind="warn" label={t('Cancelar y avisar a {n}', { n })} disabled={typed.trim() !== dateHint} onPress={() => onSend(slot)} style={{ marginTop: 12 }} />
      <Txt kind="small" color="muted" style={{ textAlign: 'center', marginTop: 8 }}>{t('Tendrás 10 segundos para deshacer antes de que salga nada.')}</Txt>
    </Sheet>
  );
}
