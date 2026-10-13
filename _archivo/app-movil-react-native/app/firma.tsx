// After paying: the waiver, signed with the finger. It never blocks the booking. No medical questionnaire
// (decision of 13/10/2026): the app does not ask for or keep health data.
import { router, useLocalSearchParams } from 'expo-router';
import React, { useMemo, useRef, useState } from 'react';
import { PanResponder, View } from 'react-native';
import Svg, { Path } from 'react-native-svg';
import { CENTRE, PROFILE } from '@/demo';
import { Icon } from '@/icons';
import { useApp } from '@/store';
import { Btn, Card, haptic, Press, Row, Screen, Tag, Txt } from '@/ui';

export default function Firma() {
  const { t, c, bookings, updateBooking } = useApp();
  const { code } = useLocalSearchParams<{ code?: string }>();
  const booking = bookings.find((b) => b.code === code) ?? bookings.find((b) => !b.waiver && !b.cancelled);
  const [strokes, setStrokes] = useState<string[]>([]);
  const current = useRef('');
  const [, redraw] = useState(0);
  const pan = useMemo(() => PanResponder.create({
    onStartShouldSetPanResponder: () => true,
    onMoveShouldSetPanResponder: () => true,
    onPanResponderGrant: (e) => { current.current = `M${e.nativeEvent.locationX.toFixed(1)} ${e.nativeEvent.locationY.toFixed(1)}`; redraw((x) => x + 1); },
    onPanResponderMove: (e) => { current.current += ` L${e.nativeEvent.locationX.toFixed(1)} ${e.nativeEvent.locationY.toFixed(1)}`; redraw((x) => x + 1); },
    onPanResponderRelease: () => { const d = current.current; current.current = ''; setStrokes((s) => [...s, d]); },
  }), []);
  const signed = strokes.length > 0;

  const item = (done: boolean, title: string, text: string) => (
    <Card key={title} style={{ padding: 14, flexDirection: 'row', gap: 12, alignItems: 'center' }}>
      <View style={{ width: 34, height: 34, borderRadius: 17, alignItems: 'center', justifyContent: 'center', backgroundColor: done ? c.accent : 'transparent', borderWidth: done ? 0 : 2, borderColor: c.warn }}>
        <Icon name={done ? 'check' : 'pen'} size={16} color={done ? c.onAccent : c.warn} stroke={2.4} />
      </View>
      <View style={{ flex: 1 }}><Txt kind="title">{title}</Txt><Txt kind="small" color="muted">{text}</Txt></View>
      <Tag tone={done ? 'ok' : 'warn'} label={done ? t('Listo') : t('Pendiente')} />
    </Card>
  );

  return (
    <Screen bottom={40}>
      <Press accessibilityRole="button" onPress={() => router.back()} style={{ flexDirection: 'row', alignItems: 'center', gap: 4, minHeight: 44, alignSelf: 'flex-start' }}>
        <Icon name="back" color={c.accentText} />
        <Txt color="accent" style={{ fontWeight: '700' }}>{t('Volver')}</Txt>
      </Press>
      <Txt kind="h1">{t('Antes de tu inmersión')}</Txt>
      {booking ? <Txt color="muted" style={{ marginTop: 4 }}>{t(booking.title)} · {booking.time} · {booking.point}</Txt> : null}
      <Card style={{ padding: 14, marginVertical: 14, flexDirection: 'row', gap: 10 }}>
        <Icon name="info" size={18} color={c.accentText} />
        <Txt kind="small" style={{ flex: 1 }}>{t('Tu plaza ya está reservada. El centro solo necesita tu firma en el descargo: 1 minuto.')}</Txt>
      </Card>
      <View style={{ gap: 8 }}>
        {item(!!booking?.waiver || false, t('Descargo de responsabilidad'), CENTRE.name + ' · ' + t('versión {n}', { n: 3 }))}
        {item(true, t('Titulación'), 'Advanced Open Water · PADI')}
        {item(true, t('Seguro y tallas'), t('Seguro hasta {d} · traje {s} · escarpines {b}', { d: PROFILE.insurance, s: PROFILE.sizes.suit, b: PROFILE.sizes.boot }))}
      </View>

      {booking && !booking.waiver ? (
        <Card strong style={{ padding: 16, marginTop: 16 }}>
          <Txt kind="title">{t('Descargo de responsabilidad')}</Txt>
          <Txt kind="small" color="muted" style={{ marginTop: 6 }}>{t('Declaro que conozco los riesgos del buceo, que seguiré las indicaciones del guía y que la información que he dado es cierta.')}</Txt>
          <View {...pan.panHandlers} accessibilityLabel={t('Firma con el dedo')} style={{ marginTop: 12, height: 150, borderRadius: 18, borderWidth: 1.5, borderStyle: 'dashed', borderColor: c.line, backgroundColor: c.surface }}>
            <Svg width="100%" height="100%" pointerEvents="none">
              {[...strokes, current.current].filter(Boolean).map((d, i) => <Path key={i} d={d} stroke={c.text} strokeWidth={3} fill="none" strokeLinecap="round" strokeLinejoin="round" />)}
            </Svg>
            {!signed ? <Txt kind="small" color="muted" style={{ position: 'absolute', left: 14, bottom: 10 }}>{t('Firma con el dedo · {n}', { n: PROFILE.name })}</Txt> : null}
          </View>
          <Row style={{ marginTop: 10 }}>
            <Btn kind="link" label={t('Borrar')} onPress={() => setStrokes([])} />
            <Btn label={t('Firmar y seguir')} disabled={!signed} onPress={() => { updateBooking(booking.code, { waiver: true }); haptic('success'); router.back(); }} style={{ flex: 1 }} />
          </Row>
        </Card>
      ) : null}
    </Screen>
  );
}
