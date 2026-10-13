// The next days at a glance (departures and occupancy). Creating and editing departures arrives in version 0.2,
// with the real server.
import React from 'react';
import { View } from 'react-native';
import { dayDate, slotsFor } from '@/demo';
import { shortDate } from '@/i18n';
import { useApp } from '@/store';
import { Card, Row, Screen, Txt } from '@/ui';

export default function CentroAgenda() {
  const { t, lang, c } = useApp();
  return (
    <Screen>
      <Txt kind="h1">{t('Agenda')}</Txt>
      <Txt kind="small" color="muted" style={{ marginTop: 4, marginBottom: 14 }}>{t('Los próximos 7 días. Crear y editar salidas llega con la versión conectada al servidor.')}</Txt>
      <View style={{ gap: 10 }}>
        {Array.from({ length: 7 }, (_, d) => d).map((d) => {
          const list = slotsFor(d);
          return (
            <Card key={d} style={{ padding: 14 }}>
              <Txt kind="title">{d === 0 ? t('Hoy') : d === 1 ? t('Mañana') : shortDate(lang, dayDate(d))}</Txt>
              {list.map((s) => {
                const booked = Math.max(1, 10 - s.spots);
                return (
                  <Row key={s.id} style={{ paddingVertical: 8, borderTopWidth: 1, borderColor: c.line, marginTop: 6 }}>
                    <Txt kind="small" style={{ fontWeight: '800', width: 48 }}>{s.time}</Txt>
                    <Txt kind="small" style={{ flex: 1 }}>{t(s.title)} · {s.point}</Txt>
                    <Txt kind="small" color="muted" style={{ fontWeight: '700' }}>{booked}/{booked + s.spots}</Txt>
                  </Row>
                );
              })}
            </Card>
          );
        })}
      </View>
    </Screen>
  );
}
