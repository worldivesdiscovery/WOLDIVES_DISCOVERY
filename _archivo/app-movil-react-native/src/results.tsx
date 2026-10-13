// Results of the timed tests kept on this phone (acceptance criterion of the brief: 5 people who never used the
// app book in < 30 s; a centre finds who dives tomorrow and the equipment in < 10 s).
import React from 'react';
import { View } from 'react-native';
import { seconds } from './i18n';
import { TestKind, useApp } from './store';
import { Card, Row, Txt } from './ui';

export function Results({ kind }: { kind: TestKind }) {
  const { t, lang, results, c } = useApp();
  const mine = results.filter((r) => r.kind === kind);
  const limit = kind === 'reserva' ? 30000 : 10000;
  const okCount = mine.filter((r) => r.ms < limit && (kind !== 'reserva' || r.taps <= 3)).length;
  return (
    <View>
      <Txt kind="label" color="muted" style={{ marginTop: 18, marginBottom: 8 }}>{t('RESULTADOS DE LAS PRUEBAS')}</Txt>
      <Card style={{ paddingHorizontal: 14, paddingVertical: 6 }}>
        {mine.length === 0 ? <Txt kind="small" color="muted" style={{ paddingVertical: 10 }}>{t('Todavía no hay pruebas en este móvil. Se lanzan desde la pantalla de inicio de la versión de pruebas.')}</Txt> : (
          <>
            <Txt kind="small" style={{ fontWeight: '800', paddingVertical: 8 }}>{t('{a} de {b} dentro del objetivo', { a: okCount, b: mine.length })}</Txt>
            {mine.map((r) => {
              const ok = r.ms < limit && (kind !== 'reserva' || r.taps <= 3);
              return (
                <Row key={r.at} style={{ paddingVertical: 9, borderTopWidth: 1, borderColor: c.line }}>
                  <Txt kind="small" color="muted">{kind === 'reserva' ? (r.firstTime ? t('Primera vez') : t('Con cuenta')) : t('Centro')}</Txt>
                  <Txt kind="small">{seconds(lang, r.ms)} · {t('{n} toques', { n: r.taps })}</Txt>
                  <Txt kind="small" color={ok ? 'accent' : 'warn'} style={{ fontWeight: '800' }}>{ok ? t('Dentro') : t('Fuera')}</Txt>
                </Row>
              );
            })}
          </>
        )}
      </Card>
    </View>
  );
}
