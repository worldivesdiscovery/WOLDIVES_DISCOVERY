// Settings of the centre (read-only in version 0.1) and the results of the centre's timed test.
import { router } from 'expo-router';
import React from 'react';
import { View } from 'react-native';
import { CENTRE } from '@/demo';
import { Icon, IconName } from '@/icons';
import { Results } from '@/results';
import { useApp } from '@/store';
import { Btn, Card, Screen, Txt } from '@/ui';

export default function CentroMas() {
  const { t, c, reset } = useApp();
  const item = (icon: IconName, title: string, text: string) => (
    <Card key={title} style={{ padding: 14, flexDirection: 'row', gap: 12, alignItems: 'center' }}>
      <View style={{ width: 40, height: 40, borderRadius: 20, backgroundColor: c.surface2, alignItems: 'center', justifyContent: 'center' }}><Icon name={icon} color={c.accentText} /></View>
      <View style={{ flex: 1 }}><Txt kind="title">{title}</Txt><Txt kind="small" color="muted">{text}</Txt></View>
    </Card>
  );
  return (
    <Screen>
      <Txt kind="h1">{t('Más')}</Txt>
      <View style={{ gap: 10, marginTop: 14 }}>
        {item('chat', t('WhatsApp del centro'), t('Conectado: {n}. Los avisos salen de tu número y las respuestas te llegan a ti.', { n: '+34 ' + CENTRE.phoneText }))}
        {item('wallet', t('Cobros'), t('Stripe conectado. Sin comisión de WORLDIVES: cobras directamente en tu cuenta.'))}
        {item('bell', t('Avisos y recordatorio'), t('Recordatorio el día antes a las 18:00, por push, WhatsApp y correo.'))}
        {item('calendar', t('Calendario'), t('Suscríbete a tu iCal desde Google Calendar o el calendario del móvil.'))}
      </View>
      <Results kind="centro" />
      <Btn kind="secondary" label={t('Cambiar de perfil de prueba')} onPress={() => { reset(null); router.replace('/bienvenida'); }} count={false} style={{ marginTop: 18 }} />
    </Screen>
  );
}
