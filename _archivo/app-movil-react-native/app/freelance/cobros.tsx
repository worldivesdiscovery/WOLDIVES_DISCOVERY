// Payments (direct bookings are charged on the freelance's own Stripe account, without commission; what a centre
// pays for a job goes outside the app with an invoice and is noted here) and documents with their expiry.
import { router } from 'expo-router';
import React from 'react';
import { View } from 'react-native';
import { dayDate, FREELANCE } from '@/demo';
import { money, shortDate } from '@/i18n';
import { useApp } from '@/store';
import { Btn, Card, Row, Screen, Tag, Txt } from '@/ui';

export default function FreelanceCobros() {
  const { t, lang, c, reset } = useApp();
  const pending = FREELANCE.payments.filter((p) => !p.paid).reduce((n, p) => n + p.amount, 0);
  return (
    <Screen>
      <Txt kind="h1">{t('Cobros')}</Txt>
      <Card style={{ padding: 16, marginTop: 14 }}>
        <Txt kind="label" color="muted">{t('PENDIENTE')}</Txt>
        <Txt kind="big">{money(lang, pending)}</Txt>
        <Txt kind="small" color="muted">{t('Reservas directas: cobro en tu cuenta de Stripe, sin comisión. Trabajos para centros: con factura, fuera de la app.')}</Txt>
      </Card>
      <Card style={{ paddingHorizontal: 14, marginTop: 10 }}>
        {FREELANCE.payments.map((p, i) => (
          <Row key={i} style={{ paddingVertical: 11, borderTopWidth: i ? 1 : 0, borderColor: c.line }}>
            <View style={{ flex: 1 }}>
              <Txt kind="small" style={{ fontWeight: '700' }}>{t(p.what)}</Txt>
              <Txt kind="small" color="muted">{p.day === 0 ? t('Hoy') : shortDate(lang, dayDate(p.day))}</Txt>
            </View>
            <View style={{ alignItems: 'flex-end', gap: 4 }}>
              <Txt kind="title">{money(lang, p.amount)}</Txt>
              <Tag tone={p.paid ? 'ok' : 'warn'} label={p.paid ? t('Cobrado') : t('Pendiente')} />
            </View>
          </Row>
        ))}
      </Card>
      <Txt kind="label" color="muted" style={{ marginTop: 18, marginBottom: 8 }}>{t('DOCUMENTOS')}</Txt>
      <Card style={{ paddingHorizontal: 14 }}>
        {FREELANCE.documents.map((d, i) => (
          <Row key={d.name} style={{ paddingVertical: 11, borderTopWidth: i ? 1 : 0, borderColor: c.line }}>
            <Txt kind="small" style={{ flex: 1, fontWeight: '700' }}>{t(d.name)}</Txt>
            <Tag tone={d.days <= 45 ? 'warn' : 'ok'} label={d.days <= 45 ? t('Caduca en {n} días', { n: d.days }) : t('Vigente')} />
          </Row>
        ))}
      </Card>
      <Btn kind="secondary" label={t('Cambiar de perfil de prueba')} onPress={() => { reset(null); router.replace('/bienvenida'); }} count={false} style={{ marginTop: 18 }} />
    </Screen>
  );
}
