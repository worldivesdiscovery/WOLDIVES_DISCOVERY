// Profile: what is saved once (certification, sizes, insurance) so booking takes seconds. Without an account,
// only the centre's information and its phone. Also: language, theme, the results of the timed tests.
import { router } from 'expo-router';
import React from 'react';
import { Linking, View } from 'react-native';
import { CENTRE, dayDate, HISTORY, PROFILE } from '@/demo';
import { LANGS, shortDate } from '@/i18n';
import { ThemePref, useApp } from '@/store';
import { Btn, Card, Chip, Row, Screen, Tag, Txt } from '@/ui';
import { Results } from '@/results';

export default function Perfil() {
  const { t, c, lang, set, theme, firstTime, reset } = useApp();
  const line = (label: string, value: string, tag?: string) => (
    <Row key={label} style={{ paddingVertical: 13, borderBottomWidth: 1, borderColor: c.line }}>
      <Txt>{label}</Txt>
      <View style={{ flexDirection: 'row', gap: 8, alignItems: 'center', flexShrink: 1 }}>
        {tag ? <Tag tone="ok" label={tag} /> : null}
        <Txt kind="small" color="muted" style={{ flexShrink: 1, textAlign: 'right' }}>{value}</Txt>
      </View>
    </Row>
  );
  return (
    <Screen>
      {firstTime ? (
        <Card style={{ padding: 16, gap: 10 }}>
          <Txt kind="h2">{t('Aún no tienes cuenta')}</Txt>
          <Txt color="muted">{t('Sin cuenta puedes ver salidas, precios y la información del centro. La cuenta se crea con tu primera reserva, con Google o Apple.')}</Txt>
          <Btn kind="secondary" icon="phone" label={t('Llamar al centro · {n}', { n: CENTRE.phoneText })} onPress={() => Linking.openURL('tel:' + CENTRE.phone)} />
          <Btn kind="secondary" icon="chat" label={t('WhatsApp del centro')} onPress={() => Linking.openURL('https://wa.me/' + CENTRE.whatsapp)} />
        </Card>
      ) : (
        <>
          <Row style={{ justifyContent: 'flex-start', gap: 14 }}>
            <View style={{ width: 64, height: 64, borderRadius: 32, backgroundColor: c.accent, alignItems: 'center', justifyContent: 'center' }}>
              <Txt kind="h2" color="onAccent">{PROFILE.initials}</Txt>
            </View>
            <View>
              <Txt kind="h1" style={{ fontSize: 26 }}>{PROFILE.name}</Txt>
              <Txt kind="small" color="muted">{PROFILE.cert}</Txt>
            </View>
          </Row>
          <View style={{ flexDirection: 'row', gap: 8, marginTop: 16 }}>
            {[[String(PROFILE.dives), t('inmersiones')], [PROFILE.maxDepth + ' m', t('máxima')], [String(PROFILE.sites), t('puntos distintos')]].map(([v, l]) => (
              <Card key={l} style={{ flex: 1, padding: 12, alignItems: 'center' }}><Txt kind="h2">{v}</Txt><Txt kind="small" color="muted" style={{ fontWeight: '700' }}>{l}</Txt></Card>
            ))}
          </View>
          <Txt kind="label" color="muted" style={{ marginTop: 18, marginBottom: 4 }}>{t('SE GUARDA UNA VEZ')}</Txt>
          <Card style={{ paddingHorizontal: 14 }}>
            {line(t('Titulaciones'), 'Advanced Open Water · Nitrox', t('Comprobada'))}
            {line(t('Tallas'), t('Traje {s} · escarpines {b} · chaleco {c}', { s: PROFILE.sizes.suit, b: PROFILE.sizes.boot, c: PROFILE.sizes.bcd }))}
            {line(t('Seguro de buceo'), t('Hasta {d}', { d: PROFILE.insurance }))}
          </Card>
          <Txt kind="label" color="muted" style={{ marginTop: 18, marginBottom: 4 }}>{t('LOGBOOK')}</Txt>
          <Card style={{ paddingHorizontal: 14 }}>
            {HISTORY.map((h) => line(h.point, `${shortDate(lang, dayDate(h.day))} · ${h.depth} m · ${h.minutes} min`))}
          </Card>
        </>
      )}

      <Txt kind="label" color="muted" style={{ marginTop: 18, marginBottom: 8 }}>{t('IDIOMA')}</Txt>
      <View style={{ flexDirection: 'row', gap: 8 }}>{LANGS.map((l) => <Chip key={l.code} label={l.label} on={lang === l.code} onPress={() => set({ lang: l.code })} />)}</View>
      <Txt kind="label" color="muted" style={{ marginTop: 18, marginBottom: 8 }}>{t('ASPECTO')}</Txt>
      <View style={{ flexDirection: 'row', gap: 8 }}>
        {([['oscuro', 'Océano (oscuro)'], ['claro', 'Superficie (claro)'], ['sistema', 'Sistema']] as [ThemePref, string][]).map(([k, l]) => <Chip key={k} label={t(l)} on={theme === k} onPress={() => set({ theme: k })} />)}
      </View>

      <Results kind="reserva" />

      <Txt kind="label" color="muted" style={{ marginTop: 18, marginBottom: 8 }}>{t('VERSIÓN DE PRUEBAS')}</Txt>
      <Card style={{ padding: 14, gap: 6 }}>
        <Txt kind="small" color="muted">{t('WORLDIVES 0.1 · datos de ejemplo, sin pagos reales. El estado del mar será de las boyas de Puertos del Estado.')}</Txt>
        <Btn kind="secondary" label={t('Cambiar de perfil de prueba')} onPress={() => { reset(null); router.replace('/bienvenida'); }} count={false} />
      </Card>
    </Screen>
  );
}
