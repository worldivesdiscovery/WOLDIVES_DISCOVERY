// The diver's bookings: QR that works without signal, the centre's WhatsApp (no chat in the app), how to get there,
// change or cancel in 2 taps with the centre's policy, and «Repetir» from the history.
import { router } from 'expo-router';
import React, { useState } from 'react';
import { Image, Linking, View } from 'react-native';
import { Booking, CENTRE, dayDate, HISTORY, nextSame, slotsFor } from '@/demo';
import { money, shortDate } from '@/i18n';
import { useApp } from '@/store';
import { Btn, Card, Chip, haptic, Press, QR, Row, Screen, Sheet, Tag, Txt } from '@/ui';
import { PHOTOS } from '@/photos';

export default function Reservas() {
  const { t, lang, bookings, updateBooking } = useApp();
  const [tab, setTab] = useState<'proximas' | 'historial'>('proximas');
  const [edit, setEdit] = useState<Booking | null>(null);
  const [done, setDone] = useState('');
  const upcoming = bookings.filter((b) => b.day >= 0).sort((a, b) => a.day - b.day || a.time.localeCompare(b.time));
  const when = (d: number, time: string) => (d === 0 ? t('Hoy') : d === 1 ? t('Mañana') : shortDate(lang, dayDate(d))) + ' · ' + time;

  // Centre policy: free cancellation up to 48 h before; after that the refund is 50 %.
  const refundOf = (b: Booking) => (b.day >= 2 ? b.amount : Math.round(b.amount * CENTRE.policy.refundPct) / 100);
  const options = edit ? [edit.day + 1, edit.day + 2, edit.day + 3].flatMap((d) => slotsFor(d).filter((s) => s.service === edit.service).slice(0, 1)) : [];

  return (
    <Screen>
      <Txt kind="h1">{t('Reservas')}</Txt>
      <View style={{ flexDirection: 'row', gap: 8, marginVertical: 14 }}>
        <Chip label={t('Próximas · {n}', { n: upcoming.filter((b) => !b.cancelled).length })} on={tab === 'proximas'} onPress={() => setTab('proximas')} />
        <Chip label={t('Historial · {n}', { n: HISTORY.length })} on={tab === 'historial'} onPress={() => setTab('historial')} />
      </View>

      {tab === 'proximas' ? (
        <View style={{ gap: 12 }}>
          {upcoming.length === 0 ? <Card style={{ padding: 16 }}><Txt color="muted">{t('Todavía no tienes reservas.')}</Txt></Card> : null}
          {upcoming.map((b) => (
            <Card key={b.code} style={{ opacity: b.cancelled ? 0.6 : 1 }}>
              <Image source={PHOTOS[b.service === 'doble' ? 'buceadores' : 'arrecife']} style={{ width: '100%', height: 96 }} resizeMode="cover" />
              <View style={{ padding: 16 }}>
                <Txt kind="label" color={b.cancelled ? 'warn' : 'accent'}>{b.cancelled ? t('CANCELADA · DEVOLUCIÓN DE {p}', { p: money(lang, b.refund ?? 0) }) : when(b.day, b.time).toUpperCase()}</Txt>
                <Txt kind="h2" style={{ fontSize: 20, marginTop: 4 }}>{t(b.title)}</Txt>
                <Txt kind="small" color="muted">{b.point} · {CENTRE.name}</Txt>
                {!b.cancelled ? (
                  <>
                    <Row style={{ justifyContent: 'flex-start', gap: 14, marginTop: 12 }}>
                      <QR value={'worldives:reserva:' + b.code} size={96} />
                      <View style={{ flex: 1 }}>
                        <Txt kind="title">{b.code}</Txt>
                        <Txt kind="small" color="muted">{b.meet}</Txt>
                        <Txt kind="small" color="accent" style={{ fontWeight: '700', marginTop: 4 }}>{t('El QR funciona sin cobertura')}</Txt>
                      </View>
                    </Row>
                    {!b.waiver ? (
                      <Press accessibilityRole="button" onPress={() => router.push({ pathname: '/firma', params: { code: b.code } })} style={{ marginTop: 12, alignSelf: 'flex-start' }}>
                        <Tag tone="warn" icon="alert" label={t('Falta firmar el descargo · Firmar')} />
                      </Press>
                    ) : <View style={{ marginTop: 12 }}><Tag tone="ok" icon="check" label={t('Descargo firmado')} /></View>}
                    <View style={{ flexDirection: 'row', gap: 8, marginTop: 12 }}>
                      <Btn kind="secondary" icon="chat" label={t('WhatsApp')} onPress={() => Linking.openURL('https://wa.me/' + CENTRE.whatsapp)} style={{ flex: 1, paddingHorizontal: 6 }} />
                      <Btn kind="secondary" icon="route" label={t('Cómo llegar')} onPress={() => Linking.openURL(CENTRE.maps)} style={{ flex: 1, paddingHorizontal: 6 }} />
                    </View>
                    <Btn kind="link" label={t('Cambiar o cancelar')} onPress={() => setEdit(b)} />
                  </>
                ) : null}
              </View>
            </Card>
          ))}
        </View>
      ) : (
        <View style={{ gap: 10 }}>
          {HISTORY.map((h) => {
            const again = nextSame(h.service, h.point);
            return (
              <Card key={h.day} style={{ padding: 14, flexDirection: 'row', gap: 12, alignItems: 'center' }}>
                <View style={{ flex: 1 }}>
                  <Txt kind="title">{t(h.title)}</Txt>
                  <Txt kind="small" color="muted">{shortDate(lang, dayDate(h.day))} · {h.point} · {h.depth} m · {h.minutes} min</Txt>
                </View>
                {again ? <Btn label={t('Repetir')} onPress={() => router.push({ pathname: '/buceador/inicio', params: { repetir: again.id } })} style={{ minHeight: 44 }} /> : null}
              </Card>
            );
          })}
        </View>
      )}

      <Sheet visible={!!edit} onClose={() => setEdit(null)} label={t('Cambiar o cancelar')}>
        {edit ? (
          <View style={{ gap: 10 }}>
            <Txt kind="h2">{t('Cambiar o cancelar')}</Txt>
            <Txt kind="small" color="muted">{t('Cancelación gratis hasta {h} h antes; después se devuelve el {p} %.', { h: CENTRE.policy.freeHours, p: CENTRE.policy.refundPct })}</Txt>
            <Txt kind="label" color="muted" style={{ marginTop: 6 }}>{t('CAMBIAR A OTRA FECHA')}</Txt>
            {options.map((s) => (
              <Btn key={s.id} kind="secondary" label={when(s.day, s.time) + ' · ' + s.point} onPress={() => { updateBooking(edit.code, { day: s.day, time: s.time, slotId: s.id, point: s.point }); haptic('success'); setEdit(null); setDone(t('Cambiada a {d}', { d: when(s.day, s.time) })); }} />
            ))}
            <Btn kind="warn" style={{ marginTop: 8 }}
              label={edit.amount > 0 ? t('Cancelar y devolver {p}', { p: money(lang, refundOf(edit)) }) : t('Cancelar sin coste')}
              onPress={() => { updateBooking(edit.code, { cancelled: true, refund: refundOf(edit) }); haptic('warning'); setEdit(null); setDone(t('Cancelada. La devolución llega a tu tarjeta en unos días.')); }} />
          </View>
        ) : null}
      </Sheet>
      {done ? (
        <Press accessibilityRole="button" onPress={() => setDone('')} style={{ marginTop: 14 }}>
          <Card strong style={{ padding: 14 }}><Txt kind="small" style={{ fontWeight: '700' }}>{done}</Txt></Card>
        </Press>
      ) : null}
    </Screen>
  );
}
