// Offers of work from the centres: accept or reject with one tap.
import React from 'react';
import { View } from 'react-native';
import { dayDate, FREELANCE } from '@/demo';
import { money, shortDate } from '@/i18n';
import { useApp } from '@/store';
import { Btn, Card, haptic, Row, Screen, Tag, Txt } from '@/ui';

export default function FreelanceTrabajos() {
  const { t, lang, offers, set } = useApp();
  const answer = (id: string, v: 'ok' | 'no') => { set({ offers: { ...offers, [id]: v } }); haptic(v === 'ok' ? 'success' : 'light'); };
  return (
    <Screen>
      <Txt kind="h1">{t('Trabajos')}</Txt>
      <Txt kind="small" color="muted" style={{ marginTop: 4, marginBottom: 14 }}>{t('Ofertas de los centros para tus días abiertos.')}</Txt>
      <View style={{ gap: 10 }}>
        {FREELANCE.offers.map((o) => {
          const a = offers[o.id];
          return (
            <Card key={o.id} style={{ padding: 16 }}>
              <Row><Txt kind="h2" style={{ fontSize: 18 }}>{shortDate(lang, dayDate(o.day))} · {o.time}</Txt><Txt kind="h2" style={{ fontSize: 18 }}>{money(lang, o.fee)}</Txt></Row>
              <Txt kind="title" style={{ marginTop: 4 }}>{t(o.what)}</Txt>
              <Txt kind="small" color="muted">{o.where}</Txt>
              {a ? (
                <View style={{ marginTop: 12 }}><Tag tone={a === 'ok' ? 'ok' : 'plain'} label={a === 'ok' ? t('Aceptado: ya está en tu agenda y el centro lo ve') : t('Rechazado: el centro lo sabe al momento')} /></View>
              ) : (
                <View style={{ flexDirection: 'row', gap: 8, marginTop: 12 }}>
                  <Btn kind="secondary" label={t('Rechazar')} onPress={() => answer(o.id, 'no')} style={{ flex: 1 }} />
                  <Btn label={t('Aceptar')} onPress={() => answer(o.id, 'ok')} style={{ flex: 1 }} />
                </View>
              )}
            </Card>
          );
        })}
      </View>
    </Screen>
  );
}
