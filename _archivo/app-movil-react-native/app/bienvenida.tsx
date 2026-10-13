// Version 0.1 (test): there are no real accounts yet, so the person chooses which side of the app to see.
// From here the two timed tests of the brief also start (book in < 30 s; the centre finds tomorrow in < 10 s).
import { router } from 'expo-router';
import React from 'react';
import { Image, View } from 'react-native';
import { LANGS } from '@/i18n';
import { Role, useApp } from '@/store';
import { Btn, Card, Chip, Press, Screen, Txt } from '@/ui';
import { Icon, IconName } from '@/icons';

const LOGO = require('../assets/splash-icon.png');

export default function Bienvenida() {
  const { t, c, reset, set, lang, startTest } = useApp();
  const go = (role: Role, firstTime = false) => {
    reset(role, firstTime);
    router.replace(role === 'buceador' ? '/buceador/inicio' : role === 'centro' ? '/centro/hoy' : '/freelance/hoy');
  };
  const option = (icon: IconName, title: string, text: string, onPress: () => void) => (
    <Press key={title} accessibilityRole="button" onPress={onPress} count={false}>
      <Card style={{ padding: 16, flexDirection: 'row', gap: 14, alignItems: 'center' }}>
        <View style={{ width: 44, height: 44, borderRadius: 22, backgroundColor: c.surface2, alignItems: 'center', justifyContent: 'center' }}>
          <Icon name={icon} color={c.accentText} />
        </View>
        <View style={{ flex: 1 }}>
          <Txt kind="title">{title}</Txt>
          <Txt kind="small" color="muted">{text}</Txt>
        </View>
        <Icon name="chevron" color={c.muted} />
      </Card>
    </Press>
  );
  return (
    <Screen bottom={40}>
      <View style={{ alignItems: 'center', marginTop: 10, marginBottom: 18 }}>
        <Image source={LOGO} style={{ width: 92, height: 92 }} resizeMode="contain" accessibilityIgnoresInvertColors />
        <Txt kind="big" style={{ marginTop: 10 }}>WORLDIVES</Txt>
        <Txt kind="small" color="muted" style={{ textAlign: 'center', marginTop: 4 }}>{t('Versión de pruebas 0.1 · datos de ejemplo, sin pagos reales')}</Txt>
      </View>

      <Txt kind="label" color="muted" style={{ marginBottom: 8 }}>{t('VER LA APP COMO')}</Txt>
      <View style={{ gap: 10 }}>
        {option('user', t('Buceador con cuenta'), t('Titulación y tallas guardadas: reserva en 2 toques.'), () => go('buceador'))}
        {option('ticket', t('Buceador por primera vez'), t('Sin cuenta: el botón de pago crea la cuenta con Google o Apple.'), () => go('buceador', true))}
        {option('sun', t('Centro de buceo'), t('Hoy, mañana, equipo a preparar y check-in con QR.'), () => go('centro'))}
        {option('briefcase', t('Freelance'), t('Tu día, tu agenda y las ofertas de los centros.'), () => go('freelance'))}
      </View>

      <Txt kind="label" color="muted" style={{ marginTop: 22, marginBottom: 8 }}>{t('PRUEBAS CRONOMETRADAS')}</Txt>
      <Card style={{ padding: 16, gap: 10 }}>
        <Txt kind="small" color="muted">{t('Dale el móvil a alguien que no conozca la app. El cronómetro empieza al pulsar y se para solo.')}</Txt>
        <Btn icon="timer" label={t('Reservar en menos de 30 s (primera vez)')} onPress={() => { reset('buceador', true); startTest('reserva', true); router.replace('/buceador/inicio'); }} count={false} />
        <Btn kind="secondary" icon="timer" label={t('Reservar en menos de 30 s (con cuenta)')} onPress={() => { reset('buceador', false); startTest('reserva', false); router.replace('/buceador/inicio'); }} count={false} />
        <Btn kind="secondary" icon="timer" label={t('Centro: quién bucea mañana (10 s)')} onPress={() => { reset('centro'); startTest('centro', false); router.replace('/centro/hoy'); }} count={false} />
      </Card>

      <Txt kind="label" color="muted" style={{ marginTop: 22, marginBottom: 8 }}>{t('IDIOMA')}</Txt>
      <View style={{ flexDirection: 'row', gap: 8 }}>
        {LANGS.map((l) => <Chip key={l.code} label={l.label} on={lang === l.code} onPress={() => set({ lang: l.code })} />)}
      </View>
    </Screen>
  );
}
