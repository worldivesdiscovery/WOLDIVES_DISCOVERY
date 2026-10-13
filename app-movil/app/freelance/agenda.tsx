// Availability: one tap blocks or opens a day. Centres only offer work on open days.
import React from 'react';
import { View } from 'react-native';
import { dayDate, FREELANCE } from '@/demo';
import { weekday } from '@/i18n';
import { useApp } from '@/store';
import { Card, haptic, Press, Screen, Txt } from '@/ui';

export default function FreelanceAgenda() {
  const { t, c, lang, blocked, set } = useApp();
  const days = Array.from({ length: 14 }, (_, i) => i);
  const kind = (d: number) => (FREELANCE.busy.includes(d) ? 'busy' : blocked.includes(d) ? 'blocked' : 'open');
  const open = days.filter((d) => kind(d) === 'open').length;
  return (
    <Screen>
      <Txt kind="h1">{t('Agenda')}</Txt>
      <Txt kind="small" color="muted" style={{ marginTop: 4, marginBottom: 14 }}>{t('Toca un día para bloquearlo o abrirlo. Los centros solo te ofrecen trabajo en días abiertos.')}</Txt>
      <View style={{ flexDirection: 'row', flexWrap: 'wrap', gap: 8 }}>
        {days.map((d) => {
          const k = kind(d);
          const date = dayDate(d);
          const bg = k === 'blocked' ? c.warnBg : c.surface;
          const fg = k === 'blocked' ? c.warn : c.text;
          return (
            <Press key={d} accessibilityRole="button" accessibilityState={{ selected: k === 'blocked', disabled: k === 'busy' }}
              accessibilityLabel={`${weekday(lang, date)} ${date.getDate()}: ${k === 'busy' ? t('con trabajo') : k === 'blocked' ? t('bloqueado') : t('abierto')}`}
              disabled={k === 'busy'}
              onPress={() => { haptic(); set({ blocked: k === 'blocked' ? blocked.filter((x) => x !== d) : [...blocked, d] }); }}
              style={{ width: '22.5%', minHeight: 78, borderRadius: 18, alignItems: 'center', justifyContent: 'center', backgroundColor: bg, borderWidth: k === 'busy' ? 1.5 : 0, borderColor: c.accent }}>
              <Txt kind="label" style={{ color: fg }}>{weekday(lang, date, true).toUpperCase()}</Txt>
              <Txt kind="h2" style={{ color: fg }}>{date.getDate()}</Txt>
              <Txt kind="label" style={{ color: k === 'busy' ? c.accentText : fg, fontSize: 9 }}>{k === 'busy' ? t('TRABAJO') : k === 'blocked' ? t('BLOQUEADO') : t('ABIERTO')}</Txt>
            </Press>
          );
        })}
      </View>
      <Card style={{ padding: 14, marginTop: 14 }}>
        <Txt kind="title">{t('{a} días con trabajo · {b} abiertos · {c} bloqueados', { a: FREELANCE.busy.length, b: open, c: blocked.length })}</Txt>
        <Txt kind="small" color="muted">{t('Medio día, vacaciones y horario fijo llegan con la versión conectada al servidor.')}</Txt>
      </Card>
    </Screen>
  );
}
