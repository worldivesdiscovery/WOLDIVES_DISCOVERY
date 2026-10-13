// The freelance's day, as clear as the centre's: where, at what time and with whom.
import { router } from 'expo-router';
import React from 'react';
import { Linking, View } from 'react-native';
import { CENTRE, dayDate, FREELANCE } from '@/demo';
import { money, shortDate } from '@/i18n';
import { useApp } from '@/store';
import { Btn, Card, Row, Screen, Tag, Txt } from '@/ui';

export default function FreelanceHoy() {
  const { t, lang, offers } = useApp();
  const pending = FREELANCE.offers.filter((o) => !offers[o.id]).length;
  return (
    <Screen>
      <Txt kind="small" color="muted" style={{ fontWeight: '700' }}>{FREELANCE.name} · {t(FREELANCE.role)}</Txt>
      <Txt kind="big">{t('Hoy') + ', ' + shortDate(lang, dayDate(0))}</Txt>
      <View style={{ gap: 10, marginTop: 14 }}>
        {FREELANCE.today.map((j, i) => (
          <Card key={j.time} style={{ padding: 16 }}>
            <Row>
              <Txt kind="big" style={{ fontSize: i === 0 ? 30 : 22 }}>{j.time}</Txt>
              <Tag label={j.direct ? t('Reserva directa') : CENTRE.name} />
            </Row>
            <Txt kind="title" style={{ fontSize: 17, marginTop: 4 }}>{t(j.what)}</Txt>
            <Txt kind="small" color="muted" style={{ marginTop: 2 }}>{j.where}</Txt>
            <Txt kind="small" color="muted">{t(j.who)}</Txt>
            {i === 0 ? (
              <View style={{ flexDirection: 'row', gap: 8, marginTop: 12 }}>
                <Btn kind="secondary" icon="route" label={t('Cómo llegar')} onPress={() => Linking.openURL(CENTRE.maps)} style={{ flex: 1 }} />
                <Btn kind="secondary" icon="chat" label={t('WhatsApp')} onPress={() => Linking.openURL('https://wa.me/' + CENTRE.whatsapp)} style={{ flex: 1 }} />
              </View>
            ) : null}
          </Card>
        ))}
        <Card style={{ padding: 16 }}>
          <Row>
            <View><Txt kind="label" color="muted">{t('PENDIENTE DE COBRO')}</Txt><Txt kind="h2">{money(lang, FREELANCE.pending)}</Txt></View>
            <Txt kind="small" color="warn" style={{ fontWeight: '700', textAlign: 'right' }}>{t('Seguro de RC: caduca en {n} días', { n: 32 })}</Txt>
          </Row>
        </Card>
        {pending ? <Btn label={t('{n} ofertas de trabajo nuevas', { n: pending })} onPress={() => router.push('/freelance/trabajos')} /> : null}
      </View>
    </Screen>
  );
}
