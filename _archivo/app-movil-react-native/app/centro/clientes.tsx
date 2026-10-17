// The centre's clients. No chat (decision of 13/10/2026): WhatsApp and call, from the centre's own phone.
import React from 'react';
import { Linking, View } from 'react-native';
import { CLIENTS, dayDate } from '@/demo';
import { shortDate } from '@/i18n';
import { useApp } from '@/store';
import { Card, IconButton, Row, Screen, Txt } from '@/ui';

export default function CentroClientes() {
  const { t, lang } = useApp();
  return (
    <Screen>
      <Txt kind="h1">{t('Clientes')}</Txt>
      <Txt kind="small" color="muted" style={{ marginTop: 4, marginBottom: 14 }}>{t('Sin chat: escribe por WhatsApp o llama desde tu móvil.')}</Txt>
      <View style={{ gap: 10 }}>
        {CLIENTS.map((p) => (
          <Card key={p.name} style={{ padding: 14 }}>
            <Row>
              <View style={{ flex: 1 }}>
                <Txt kind="title">{p.name}</Txt>
                <Txt kind="small" color="muted">{t(p.level)} · {t('{n} inm.', { n: p.dives })} · {t('última: {d}', { d: shortDate(lang, dayDate(p.last)) })}</Txt>
              </View>
              <IconButton icon="chat" label={t('WhatsApp')} onPress={() => Linking.openURL('https://wa.me/' + p.phone.replace('+', ''))} />
              <IconButton icon="phone" label={t('Llamar')} onPress={() => Linking.openURL('tel:' + p.phone)} />
            </Row>
          </Card>
        ))}
      </View>
    </Screen>
  );
}
