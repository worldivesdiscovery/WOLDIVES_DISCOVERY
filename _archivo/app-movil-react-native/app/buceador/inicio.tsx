// Home of the diver: tap a departure (1) → sheet with everything (not a new screen) → pay (2) → confirmed.
// First booking without an account: the same pay button first opens the system sign-in (Google or Apple), which
// creates the account, and then the wallet. Without an account the person can still see everything and call.
import { router, useLocalSearchParams } from 'expo-router';
import React, { useEffect, useMemo, useRef, useState } from 'react';
import { Animated, Image, Linking, Modal, ScrollView, Switch, Text, View } from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { Booking, CENTRE, dayDate, findSlot, MY_RANK, PROFILE, RENT_PRICE, Slot, slotsFor, weekendOffset } from '@/demo';
import { Icon } from '@/icons';
import { money, seconds, shortDate } from '@/i18n';
import { PHOTOS } from '@/photos';
import { TestResult, useApp } from '@/store';
import { Btn, Card, Chip, Glow, haptic, IconButton, isIOS, Press, QR, Row, Screen, Sheet, SystemSheet, Tag, Txt } from '@/ui';


type DayKey = 'hoy' | 'manana' | 'finde' | 'elegir';
type PayMode = 'full' | 'deposit' | 'center';

export default function Inicio() {
  const { t, c, lang, firstTime, set, bookings, addBooking, finishTest, tap } = useApp();
  const params = useLocalSearchParams<{ repetir?: string }>();
  const [day, setDay] = useState<DayKey>('hoy');
  const [pick, setPick] = useState(7);
  const [showAll, setShowAll] = useState(false);
  const [sel, setSel] = useState<Slot | null>(null);
  const [people, setPeople] = useState(1);
  const [equip, setEquip] = useState(true);
  const [step, setStep] = useState<null | 'signin' | 'wallet'>(null);
  const [mode, setMode] = useState<PayMode>('full');
  const [done, setDone] = useState<{ booking: Booking; result: TestResult | null } | null>(null);
  const [taken, setTaken] = useState(false);
  const timer = useRef<ReturnType<typeof setTimeout> | null>(null);

  // Real time: someone else takes a place on a popular departure a few seconds after opening.
  useEffect(() => { const id = setTimeout(() => setTaken(true), 7000); return () => clearTimeout(id); }, []);
  useEffect(() => () => { if (timer.current) clearTimeout(timer.current); }, []);
  // «Repetir» from the history opens the sheet of the next date directly.
  useEffect(() => {
    if (!params.repetir) return;
    const s = findSlot(String(params.repetir));
    if (s) openSlot(s);
    router.setParams({ repetir: undefined });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [params.repetir]);

  const offset = day === 'hoy' ? 0 : day === 'manana' ? 1 : day === 'finde' ? weekendOffset() : pick;
  const all = useMemo(() => slotsFor(offset).map((s) => (s.live && taken ? { ...s, spots: s.spots - 1 } : s)), [offset, taken]);
  const list = firstTime || showAll ? all : all.filter((s) => s.rank <= MY_RANK);
  const hidden = all.length - list.length;
  const next = bookings.filter((b) => !b.cancelled && b.day >= 0).sort((a, b) => a.day - b.day || a.time.localeCompare(b.time))[0];

  function openSlot(s: Slot) {
    setSel(s); setPeople(1); setEquip(!firstTime); setMode('full');
  }
  const unit = sel ? sel.price + (equip ? RENT_PRICE : 0) : 0;
  const total = unit * people;
  const deposit = Math.round(total * 0.3);
  const apt = !!sel && (firstTime || sel.rank <= MY_RANK);

  function pay(m: PayMode) {
    setMode(m);
    if (m === 'center') return confirm('center');
    if (firstTime) {
      setStep('signin');
      if (isIOS) timer.current = setTimeout(() => afterSignin(m), 1400);
      return;
    }
    setStep('wallet');
    if (isIOS) timer.current = setTimeout(() => confirm(m), 1600);
  }
  function afterSignin(m: PayMode) {
    set({ firstTime: false });
    setStep('wallet');
    if (isIOS) timer.current = setTimeout(() => confirm(m), 1600);
  }
  function confirm(m: PayMode) {
    if (!sel) return;
    const booking: Booking = {
      code: 'WOD-' + String(Math.floor(200000 + Math.random() * 700000)), slotId: sel.id, service: sel.service, title: sel.title, point: sel.point,
      meet: sel.meet, day: sel.day, time: sel.time, people, equip, paid: m, amount: m === 'deposit' ? deposit : m === 'center' ? 0 : total, waiver: false,
    };
    addBooking(booking);
    const result = finishTest('reserva');
    haptic('success');
    setStep(null); setSel(null);
    setDone({ booking, result });
  }

  const dayLabel = (o: number) => (o === 0 ? t('Hoy') : o === 1 ? t('Mañana') : shortDate(lang, dayDate(o)));
  const sea = (s: Slot) => t('Mar {m} m · viento {k} km/h', { m: s.wave.toFixed(1).replace('.', lang === 'en' ? '.' : ','), k: s.wind });

  return (
    <Screen>
      <Row style={{ marginBottom: 14 }}>
        <View>
          <Txt kind="body" color="muted" style={{ fontWeight: '600' }}>{firstTime ? t('Buenos días') : t('Buenos días, {n}', { n: PROFILE.name.split(' ')[0] })}</Txt>
          <Txt kind="big">{firstTime ? t('¿Buceamos?') : t('¿Dónde buceamos?')}</Txt>
        </View>
        <IconButton icon="bell" label={t('Avisos')} onPress={() => router.push('/buceador/reservas')} />
      </Row>

      {next && !firstTime ? (
        <Press accessibilityRole="button" onPress={() => router.push('/buceador/reservas')}>
          <Card style={{ padding: 14, flexDirection: 'row', gap: 12, alignItems: 'center', marginBottom: 14 }}>
            <View style={{ flex: 1 }}>
              <Txt kind="label" color="accent">{t('TU PRÓXIMA INMERSIÓN')}</Txt>
              <Txt kind="title" style={{ fontSize: 17, marginTop: 3 }}>{dayLabel(next.day)} · {next.time}</Txt>
              <Txt kind="small" color="muted">{t(next.title)} · {next.point}</Txt>
            </View>
            {next.day === 0 ? (
              <View style={{ paddingHorizontal: 12, paddingVertical: 10, borderRadius: 16, backgroundColor: c.accent }}>
                <Txt kind="label" color="onAccent">{t('HOY')}</Txt>
              </View>
            ) : (
              <View style={{ alignItems: 'center', paddingHorizontal: 12, paddingVertical: 8, borderRadius: 16, backgroundColor: c.surface2 }}>
                <Txt kind="h2">{next.day}</Txt>
                <Txt kind="small" color="muted" style={{ fontWeight: '700' }}>{next.day === 1 ? t('día') : t('días')}</Txt>
              </View>
            )}
          </Card>
        </Press>
      ) : (
        <Card style={{ padding: 14, marginBottom: 14 }}>
          <Txt kind="label" color="accent">{t('PARA EMPEZAR')}</Txt>
          <Txt kind="title" style={{ fontSize: 17, marginTop: 3 }}>{t('Bautizo en Cala Granadella')}</Txt>
          <Txt kind="small" color="muted">{t('Sin titulación · con instructor')} · {money(lang, 65)}</Txt>
        </Card>
      )}

      <ScrollView horizontal showsHorizontalScrollIndicator={false} style={{ marginHorizontal: -18, marginBottom: 12 }} contentContainerStyle={{ paddingHorizontal: 18, gap: 8 }}>
        {(['hoy', 'manana', 'finde', 'elegir'] as DayKey[]).map((k) => (
          <Chip key={k} label={k === 'hoy' ? t('Hoy') : k === 'manana' ? t('Mañana') : k === 'finde' ? t('Finde') : t('Elegir')} on={day === k} onPress={() => { setDay(k); setShowAll(false); }} />
        ))}
      </ScrollView>
      {day === 'elegir' ? (
        <ScrollView horizontal showsHorizontalScrollIndicator={false} style={{ marginHorizontal: -18, marginBottom: 12 }} contentContainerStyle={{ paddingHorizontal: 18, gap: 8 }}>
          {Array.from({ length: 12 }, (_, i) => i + 2).map((o) => <Chip key={o} label={shortDate(lang, dayDate(o))} on={pick === o} onPress={() => setPick(o)} />)}
        </ScrollView>
      ) : null}

      <Row style={{ marginBottom: 10, marginHorizontal: 2 }}>
        <Txt kind="title">{day === 'hoy' ? t('Hoy') + ', ' + shortDate(lang, dayDate(0)) : day === 'manana' ? t('Mañana') + ', ' + shortDate(lang, dayDate(1)) : shortDate(lang, dayDate(offset))}</Txt>
        <Txt kind="small" color="muted" style={{ fontWeight: '700' }}>{firstTime ? t('Cerca de Xàbia') : t('Solo aptas para ti')}</Txt>
      </Row>

      <View style={{ gap: 10 }}>
        {list.map((s) => (
          <Press key={s.id} accessibilityRole="button" accessibilityLabel={`${s.time}, ${t(s.title)}, ${s.point}, ${money(lang, s.price)}, ${t('{n} plazas', { n: s.spots })}`} onPress={() => openSlot(s)}>
            <Card style={{ flexDirection: 'row', gap: 12, padding: 10 }}>
              <View style={{ width: 92, minHeight: 100, borderRadius: 16, overflow: 'hidden' }}>
                <Image source={PHOTOS[s.img]} style={{ position: 'absolute', top: 0, left: 0, right: 0, bottom: 0, width: '100%', height: '100%' }} resizeMode="cover" />
              </View>
              <View style={{ flex: 1, gap: 3, paddingVertical: 2 }}>
                <Row><Txt kind="h2" style={{ fontSize: 24 }}>{s.time}</Txt><Txt kind="title" style={{ fontSize: 18 }}>{money(lang, s.price)}</Txt></Row>
                <Txt kind="title" style={{ fontSize: 15 }}>{t(s.title)}</Txt>
                <Txt kind="small" color="muted">{s.point}</Txt>
                <View style={{ flexDirection: 'row', flexWrap: 'wrap', gap: 6, alignItems: 'center', marginTop: 2 }}>
                  <Tag label={t(s.level)} />
                  <View style={{ flexDirection: 'row', alignItems: 'center', gap: 5 }}>
                    <View style={{ width: 7, height: 7, borderRadius: 4, backgroundColor: c.accent }} />
                    <Txt kind="small" color={s.spots <= 3 ? 'warn' : 'accent'} style={{ fontWeight: '800' }}>{s.spots <= 3 ? t('Quedan {n}', { n: s.spots }) : t('{n} plazas', { n: s.spots })}</Txt>
                  </View>
                </View>
                <Txt kind="small" color="muted">{sea(s)}</Txt>
                {!firstTime && s.rank > MY_RANK ? <Txt kind="small" color="warn" style={{ fontWeight: '800' }}>{t('No apta para tu nivel')}</Txt> : null}
              </View>
            </Card>
          </Press>
        ))}
        {list.length === 0 ? <Card style={{ padding: 16 }}><Txt color="muted">{t('No quedan salidas este día.')}</Txt></Card> : null}
      </View>
      {hidden > 0 || showAll ? (
        <Btn kind="link" label={showAll ? t('Ver solo las aptas para mí') : t('{n} salidas más no son aptas para tu nivel · Ver', { n: hidden })} onPress={() => setShowAll(!showAll)} />
      ) : null}

      <Sheet visible={!!sel && !step} onClose={() => setSel(null)} label={sel ? t(sel.title) : ''}>
        {sel ? (
          <View>
            <Image source={PHOTOS[sel.img]} style={{ width: '100%', height: 150, borderRadius: 22 }} resizeMode="cover" accessibilityLabel={t('Foto del punto {p}', { p: sel.point })} />
            <Txt kind="h2" style={{ marginTop: 14 }}>{t(sel.title)}</Txt>
            <View style={{ gap: 6, marginTop: 8 }}>
              <Line icon="clock" text={`${dayLabel(sel.day)} · ${sel.time} · ${sel.dur}`} />
              <Line icon="pin" text={t('{p} · encuentro en {m}', { p: sel.point, m: sel.meet })} />
              <Line icon="wave" text={sea(sel) + ' · ' + t('datos de ejemplo')} />
            </View>
            <View style={{ flexDirection: 'row', gap: 8, marginTop: 12, padding: 12, borderRadius: 16, backgroundColor: c.surface2 }}>
              <Icon name={apt ? 'checkCircle' : 'alert'} size={19} color={apt ? c.accentText : c.warn} stroke={2.2} />
              <Txt kind="small" color={apt ? 'accent' : 'warn'} style={{ flex: 1, fontWeight: '700' }}>
                {firstTime
                  ? sel.rank === 0 ? t('Sin titulación: el instructor va contigo todo el rato.') : t('Exige {l}. Al pagar declaras que la tienes; el centro la comprueba en el muelle.', { l: t(sel.level) })
                  : apt ? t('Apta para tu Advanced Open Water.') : t('No apta: exige {l}.', { l: t(sel.level) })}
              </Txt>
            </View>

            <Row style={{ marginTop: 14 }}>
              <View>
                <Txt kind="title">{t('Personas')}</Txt>
                <Txt kind="small" color="muted">{t('{n} plazas libres ahora', { n: sel.spots })}</Txt>
              </View>
              <View style={{ flexDirection: 'row', alignItems: 'center', gap: 6 }}>
                <IconButton icon="minus" label={t('Una persona menos')} onPress={() => setPeople(Math.max(1, people - 1))} />
                <Txt kind="h2" style={{ minWidth: 28, textAlign: 'center' }} accessibilityLiveRegion="polite">{people}</Txt>
                <IconButton icon="plus" label={t('Una persona más')} onPress={() => setPeople(Math.min(sel.spots, people + 1))} />
              </View>
            </Row>
            <Row style={{ marginTop: 12 }}>
              <View style={{ flex: 1 }}>
                <Txt kind="title">{t('Alquiler de equipo · +{p}', { p: money(lang, RENT_PRICE) })}</Txt>
                <Txt kind="small" color="muted">{firstTime ? t('Las tallas te las pedimos después de pagar.') : t('Tus tallas: traje {s} · escarpines {b} · chaleco {c}', { s: PROFILE.sizes.suit, b: PROFILE.sizes.boot, c: PROFILE.sizes.bcd })}</Txt>
              </View>
              <Switch value={equip} onValueChange={(v) => { tap(); setEquip(v); }} trackColor={{ true: c.accent, false: c.surface2 }} thumbColor="#FFFFFF" accessibilityLabel={t('Alquiler de equipo')} />
            </Row>

            <Row style={{ marginTop: 16, alignItems: 'flex-end' }}>
              <Txt kind="small" color="muted" style={{ flex: 1 }}>{t('Cancelación gratis hasta {h} h antes; después se devuelve el {p} %.', { h: CENTRE.policy.freeHours, p: CENTRE.policy.refundPct })}</Txt>
              <View style={{ alignItems: 'flex-end' }}>
                <Txt kind="small" color="muted" style={{ fontWeight: '700' }}>{t('Total')}</Txt>
                <Txt kind="big">{money(lang, total)}</Txt>
              </View>
            </Row>

            {firstTime ? <Txt kind="small" color="muted" style={{ textAlign: 'center', marginTop: 12 }}>{t('Al pagar se crea tu cuenta con {p}, sin formularios.', { p: isIOS ? 'Apple' : 'Google' })}</Txt> : null}
            {apt ? (
              <>
                <Btn kind="pay" label={isIOS ? t('Reservar con Apple Pay') : t('Reservar con Google Pay')} onPress={() => pay('full')} style={{ marginTop: 12 }} />
                <View style={{ flexDirection: 'row', justifyContent: 'center', gap: 6 }}>
                  <Btn kind="link" label={t('Pagar señal de {p}', { p: money(lang, deposit) })} onPress={() => pay('deposit')} />
                  {!firstTime ? <Btn kind="link" label={t('Pagar en el centro')} onPress={() => pay('center')} /> : null}
                </View>
              </>
            ) : (
              <Btn label={t('Ver salidas aptas')} onPress={() => setSel(null)} style={{ marginTop: 12 }} />
            )}
            <View style={{ flexDirection: 'row', justifyContent: 'center', gap: 6, borderTopWidth: 1, borderColor: c.line, marginTop: 4 }}>
              <Btn kind="link" icon="chat" label={t('WhatsApp del centro')} onPress={() => Linking.openURL('https://wa.me/' + CENTRE.whatsapp)} />
              <Btn kind="link" icon="phone" label={t('Llamar')} onPress={() => Linking.openURL('tel:' + CENTRE.phone)} />
            </View>
          </View>
        ) : null}
      </Sheet>

      <SystemSheet
        visible={step === 'signin'}
        title={isIOS ? t('Iniciar sesión con Apple') : t('Iniciar sesión con Google')}
        note={t('WORLDIVES recibirá tu nombre y tu correo para crear tu cuenta.')}
        rows={[[t('Nombre'), PROFILE.name], [t('Correo'), isIOS ? t('oculto («Ocultar mi correo»)') : 'bea@example.com']]}
        footer={isIOS
          ? <SystemConfirm label={t('Continuar con Face ID')} />
          : <SystemButton label={t('Continuar como {n}', { n: PROFILE.name.split(' ')[0] })} onPress={() => afterSignin(mode)} />}
      />
      <SystemSheet
        visible={step === 'wallet'}
        title={isIOS ? 'Apple Pay' : 'Google Pay'}
        rows={[[t('Comercio'), CENTRE.name], [t('Tarjeta'), 'Visa ···· 4242'], [t('Pagar'), money(lang, mode === 'deposit' ? deposit : total)]]}
        footer={isIOS ? <SystemConfirm label={t('Confirmar con el botón lateral')} /> : <SystemButton label={t('Continuar')} onPress={() => confirm(mode)} />}
      />

      <Confirmed done={done} onClose={() => setDone(null)} />
    </Screen>
  );
}

function Line({ icon, text }: { icon: 'clock' | 'pin' | 'wave'; text: string }) {
  const { c } = useApp();
  return (
    <View style={{ flexDirection: 'row', gap: 8, alignItems: 'center' }}>
      <Icon name={icon} size={17} color={c.muted} />
      <Txt kind="small" color="muted" style={{ flex: 1 }}>{text}</Txt>
    </View>
  );
}

function SystemConfirm({ label }: { label: string }) {
  return (
    <View style={{ alignItems: 'center', gap: 8, marginTop: 14 }}>
      <Icon name="faceid" size={46} color="#3FE0C5" stroke={1.6} />
      <Text style={{ fontSize: 14, fontWeight: '600', color: '#8E8E93' }}>{label}</Text>
    </View>
  );
}

function SystemButton({ label, onPress }: { label: string; onPress: () => void }) {
  return (
    <Press accessibilityRole="button" onPress={onPress} count={false} style={{ marginTop: 16, height: 52, borderRadius: 26, backgroundColor: '#1A73E8', alignItems: 'center', justifyContent: 'center' }}>
      <Text style={{ color: '#FFFFFF', fontSize: 16, fontWeight: '700' }}>{label}</Text>
    </Press>
  );
}

function Confirmed({ done, onClose }: { done: { booking: Booking; result: TestResult | null } | null; onClose: () => void }) {
  const { t, c, lang } = useApp();
  const insets = useSafeAreaInsets();
  const scale = useRef(new Animated.Value(0.3)).current;
  useEffect(() => { if (done) { scale.setValue(0.3); Animated.spring(scale, { toValue: 1, useNativeDriver: true, friction: 5 }).start(); } }, [done, scale]);
  if (!done) return null;
  const b = done.booking;
  const r = done.result;
  const ok = r ? r.ms < 30000 && r.taps <= 3 : false;
  return (
    <Modal visible animationType="fade" onRequestClose={onClose} statusBarTranslucent>
      <View style={{ flex: 1, backgroundColor: c.bg }}>
        <Glow />
        <ScrollView contentContainerStyle={{ paddingTop: insets.top + 30, paddingHorizontal: 18, paddingBottom: insets.bottom + 30, alignItems: 'stretch' }}>
          <Animated.View style={{ alignSelf: 'center', width: 96, height: 96, borderRadius: 48, backgroundColor: c.accent, alignItems: 'center', justifyContent: 'center', transform: [{ scale }] }}>
            <Icon name="check" size={52} color={c.onAccent} stroke={2.6} />
          </Animated.View>
          <Txt kind="big" style={{ textAlign: 'center', marginTop: 16 }}>{t('Reserva confirmada')}</Txt>
          <Txt color="muted" style={{ textAlign: 'center', marginTop: 6 }}>{t('El justificante está en tu correo y en Reservas.')}</Txt>
          {r ? (
            <Card strong style={{ padding: 14, marginTop: 16, flexDirection: 'row', gap: 12, alignItems: 'center' }}>
              <Icon name="timer" size={26} color={ok ? c.accentText : c.warn} />
              <View style={{ flex: 1 }}>
                <Txt kind="title" color={ok ? 'accent' : 'warn'}>{t('{s} y {n} toques', { s: seconds(lang, r.ms), n: r.taps })}</Txt>
                <Txt kind="small" color="muted">{ok ? t('Dentro del objetivo: menos de 30 s y como mucho 3 toques.') : t('Fuera del objetivo: menos de 30 s y como mucho 3 toques.')}</Txt>
              </View>
            </Card>
          ) : null}
          <Card style={{ padding: 16, marginTop: 14, flexDirection: 'row', gap: 14, alignItems: 'center' }}>
            <QR value={'worldives:reserva:' + b.code} size={104} />
            <View style={{ flex: 1 }}>
              <Txt kind="title" style={{ fontSize: 17 }}>{t(b.title)}</Txt>
              <Txt kind="small" color="muted">{(b.day === 0 ? t('Hoy') : b.day === 1 ? t('Mañana') : shortDate(lang, dayDate(b.day))) + ' · ' + b.time}</Txt>
              <Txt kind="small" color="muted">{b.meet}</Txt>
              <Txt kind="small" color="accent" style={{ fontWeight: '800', marginTop: 4 }}>
                {b.paid === 'center' ? t('Pagas en el centro') : b.paid === 'deposit' ? t('Señal pagada: {p}', { p: money(lang, b.amount) }) : t('Pagado: {p}', { p: money(lang, b.amount) })}
              </Txt>
            </View>
          </Card>
          <Btn icon="pen" label={t('Firmar el descargo · 1 min')} onPress={() => { onClose(); router.push({ pathname: '/firma', params: { code: b.code } }); }} style={{ marginTop: 14 }} count={false} />
          <Txt kind="small" color="muted" style={{ textAlign: 'center', marginTop: 8 }}>{t('No bloquea tu reserva: puedes hacerlo hasta antes de salir.')}</Txt>
          <Btn kind="link" label={t('Volver al inicio')} onPress={onClose} count={false} style={{ marginTop: 6 }} />
        </ScrollView>
      </View>
    </Modal>
  );
}
