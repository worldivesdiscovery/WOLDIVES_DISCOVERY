// Check-in on the dock: scan the booking QR with the camera. Works without signal (the day is saved on the phone;
// in version 0.2 the check-ins are sent to the server when the signal comes back).
import { CameraView, useCameraPermissions } from 'expo-camera';
import { router, useLocalSearchParams } from 'expo-router';
import React, { useRef, useState } from 'react';
import { Platform, View } from 'react-native';
import { CENTRE_DAYS, Diver } from '@/demo';
import { Icon } from '@/icons';
import { useApp } from '@/store';
import { Btn, Card, haptic, Press, Row, Screen, Tag, Txt } from '@/ui';

type Found = { diver: Diver; slot: string } | { unknown: string };

export default function Checkin() {
  const { t, c, checkins, set } = useApp();
  const { slot: slotId } = useLocalSearchParams<{ slot?: string }>();
  const [perm, ask] = useCameraPermissions();
  const [last, setLast] = useState<Found | null>(null);
  const lastCode = useRef('');
  const slots = CENTRE_DAYS.hoy.slots;
  const slot = slots.find((s) => s.id === slotId) ?? slots.find((s) => s.id === 'c1') ?? slots[0];
  const done = slot.divers.filter((d) => d.code && checkins[d.code]).length;

  function mark(code: string) {
    const found = slots.flatMap((s) => s.divers.map((d) => ({ d, s }))).find((x) => x.d.code === code);
    if (!found) { setLast({ unknown: code }); haptic('warning'); return; }
    set({ checkins: { ...checkins, [code]: new Date().toISOString() } });
    setLast({ diver: found.d, slot: found.s.time + ' · ' + found.s.title });
    haptic(found.d.missing || !found.d.paid ? 'warning' : 'success');
  }
  function onScan({ data }: { data: string }) {
    const code = (data.match(/WOD-\d{6}/) || [''])[0];
    if (!code || code === lastCode.current) return;
    lastCode.current = code;
    setTimeout(() => { lastCode.current = ''; }, 2500);
    mark(code);
  }

  return (
    <Screen bottom={40}>
      <Row>
        <Press accessibilityRole="button" onPress={() => router.back()} style={{ flexDirection: 'row', alignItems: 'center', gap: 4, minHeight: 44 }}>
          <Icon name="back" color={c.accentText} /><Txt color="accent" style={{ fontWeight: '700' }}>{t('Hoy')}</Txt>
        </Press>
        <Tag tone="warn" icon="offline" label={t('Funciona sin cobertura')} />
      </Row>
      <Txt kind="h1">{slot.time + ' · ' + t(slot.title)}</Txt>
      <Txt color="muted">{t('Check-in {a} de {b}', { a: done, b: slot.divers.length })}</Txt>

      <View style={{ height: 230, borderRadius: 26, overflow: 'hidden', marginTop: 14, backgroundColor: '#0A2133', alignItems: 'center', justifyContent: 'center' }}>
        {perm?.granted && Platform.OS !== 'web' ? (
          <CameraView style={{ position: 'absolute', top: 0, left: 0, right: 0, bottom: 0 }} facing="back" barcodeScannerSettings={{ barcodeTypes: ['qr'] }} onBarcodeScanned={onScan} />
        ) : (
          <View style={{ alignItems: 'center', gap: 10, padding: 20 }}>
            <Icon name="scan" size={42} color="#3FE0C5" />
            <Txt style={{ color: '#EAF6FA', textAlign: 'center' }}>{t('Apunta al QR de la reserva')}</Txt>
            {Platform.OS !== 'web' ? <Btn label={t('Permitir la cámara')} onPress={() => ask()} /> : null}
          </View>
        )}
      </View>

      {last ? (
        'unknown' in last ? (
          <Card style={{ padding: 14, marginTop: 12, borderWidth: 1.5, borderColor: c.warn }}>
            <Txt kind="title" color="warn">{t('Reserva {c} no es de hoy en este centro', { c: last.unknown })}</Txt>
            <Txt kind="small" color="muted">{t('En esta versión de prueba cada móvil tiene sus propios datos de ejemplo.')}</Txt>
          </Card>
        ) : (
          <Card style={{ padding: 14, marginTop: 12, borderWidth: 1.5, borderColor: last.diver.missing || !last.diver.paid ? c.warn : c.accent }}>
            <Txt kind="title" color={last.diver.missing || !last.diver.paid ? 'warn' : 'accent'}>
              {last.diver.missing ? t('{n} · falta el {x}', { n: last.diver.name, x: t(last.diver.missing) }) : !last.diver.paid ? t('{n} · sin pagar', { n: last.diver.name }) : t('{n} · dentro', { n: last.diver.name })}
            </Txt>
            <Txt kind="small" color="muted">{t(last.diver.level)} · {t('{n} inm.', { n: last.diver.dives })} · {last.slot}</Txt>
          </Card>
        )
      ) : null}

      <Txt kind="label" color="muted" style={{ marginTop: 16, marginBottom: 4 }}>{t('BUCEADORES DE LA SALIDA')}</Txt>
      <Card style={{ paddingHorizontal: 14 }}>
        {slot.divers.map((d) => {
          const ok = !!(d.code && checkins[d.code]);
          return (
            <Row key={d.name} style={{ paddingVertical: 10, borderBottomWidth: 1, borderColor: c.line }}>
              <View style={{ width: 28, height: 28, borderRadius: 14, alignItems: 'center', justifyContent: 'center', backgroundColor: ok ? c.accent : 'transparent', borderWidth: ok ? 0 : 2, borderColor: c.line }}>
                {ok ? <Icon name="check" size={14} color={c.onAccent} stroke={2.8} /> : null}
              </View>
              <View style={{ flex: 1 }}>
                <Txt kind="small" style={{ fontWeight: '800' }}>{d.name}</Txt>
                <Txt kind="small" color={d.missing || !d.paid ? 'warn' : 'muted'}>{d.missing ? t('Falta {x}', { x: t(d.missing) }) : !d.paid ? t('Sin pagar') : t(d.level)}</Txt>
              </View>
              {!ok && d.code ? <Btn kind="secondary" label={t('Marcar')} onPress={() => mark(d.code!)} style={{ minHeight: 40 }} /> : null}
            </Row>
          );
        })}
      </Card>
    </Screen>
  );
}
