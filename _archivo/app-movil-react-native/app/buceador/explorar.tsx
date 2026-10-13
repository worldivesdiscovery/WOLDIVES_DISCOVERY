// Dive sites with filters (level, depth, type). The interactive map arrives in phase 3; here, the list.
import { router } from 'expo-router';
import React, { useState } from 'react';
import { ScrollView, View } from 'react-native';
import { nextSame, POINTS } from '@/demo';
import { Icon } from '@/icons';
import { useApp } from '@/store';
import { Btn, Card, Chip, Press, Row, Screen, Sheet, Tag, Txt } from '@/ui';

type Pt = (typeof POINTS)[number];

export default function Explorar() {
  const { t, c } = useApp();
  const [level, setLevel] = useState(-1);
  const [type, setType] = useState('');
  const [depth, setDepth] = useState(0);
  const [sel, setSel] = useState<Pt | null>(null);
  const list = POINTS.filter((p) => (level < 0 || p.rank === level) && (!type || p.type === type) && (!depth || (depth === 18 ? p.depth <= 18 : depth === 30 ? p.depth > 18 && p.depth <= 30 : p.depth > 30)));
  const row = (children: React.ReactNode) => (
    <ScrollView horizontal showsHorizontalScrollIndicator={false} style={{ marginHorizontal: -18, marginBottom: 10 }} contentContainerStyle={{ paddingHorizontal: 18, gap: 8 }}>{children}</ScrollView>
  );
  const service = (p: Pt) => (p.type === 'Costa' ? 'bautizo' : p.type === 'Nocturna' ? 'nocturna' : p.rank === 3 ? 'profunda' : p.rank === 2 ? 'doble' : 'simple');
  const point = (p: Pt) => (p.type === 'Nocturna' ? 'Cala Granadella' : p.name);

  return (
    <Screen>
      <Txt kind="h1">{t('Explorar')}</Txt>
      <Txt kind="small" color="muted" style={{ marginTop: 4, marginBottom: 14 }}>{t('Puntos de buceo cerca de Xàbia. El mapa interactivo llega en una próxima versión.')}</Txt>
      {row([[-1, 'Todos los niveles'], [0, 'Sin titulación'], [1, 'Open Water'], [2, 'Advanced']].map(([v, l]) => <Chip key={String(v)} label={t(String(l))} on={level === v} onPress={() => setLevel(Number(v))} />))}
      {row([['', 'Todo'], ['Barco', 'Barco'], ['Costa', 'Costa'], ['Nocturna', 'Nocturna']].map(([v, l]) => <Chip key={v} label={t(l)} on={type === v} onPress={() => setType(v)} />))}
      {row([[0, 'Cualquier profundidad'], [18, 'Hasta 18 m'], [30, '18–30 m'], [40, 'Más de 30 m']].map(([v, l]) => <Chip key={String(v)} label={t(String(l))} on={depth === v} onPress={() => setDepth(Number(v))} />))}
      <View style={{ gap: 10, marginTop: 4 }}>
        {list.map((p) => (
          <Press key={p.name} accessibilityRole="button" onPress={() => setSel(p)}>
            <Card style={{ padding: 14, flexDirection: 'row', gap: 12, alignItems: 'center' }}>
              <View style={{ width: 44, height: 44, borderRadius: 22, backgroundColor: c.surface2, alignItems: 'center', justifyContent: 'center' }}><Icon name="pin" color={c.accentText} /></View>
              <View style={{ flex: 1, gap: 3 }}>
                <Txt kind="title">{p.name}</Txt>
                <View style={{ flexDirection: 'row', gap: 6, flexWrap: 'wrap' }}><Tag label={t(p.type)} /><Tag label={t(p.level)} /><Tag label={p.depth + ' m'} /></View>
              </View>
              <Icon name="chevron" color={c.muted} />
            </Card>
          </Press>
        ))}
        {list.length === 0 ? <Card style={{ padding: 16 }}><Txt color="muted">{t('Ningún punto con estos filtros.')}</Txt></Card> : null}
      </View>
      <Sheet visible={!!sel} onClose={() => setSel(null)} label={sel?.name ?? ''}>
        {sel ? (
          <View style={{ gap: 8 }}>
            <Txt kind="h2">{sel.name}</Txt>
            <Row style={{ justifyContent: 'flex-start', gap: 6 }}><Tag label={t(sel.type)} /><Tag label={t(sel.level)} /><Tag label={t('Hasta {n} m', { n: sel.depth })} /></Row>
            <Txt color="muted">{t(sel.note)}</Txt>
            {(() => {
              const s = nextSame(service(sel), point(sel), 0);
              return s ? <Btn label={t('Ver la próxima salida')} onPress={() => { setSel(null); router.push({ pathname: '/buceador/inicio', params: { repetir: s.id } }); }} style={{ marginTop: 8 }} /> : null;
            })()}
          </View>
        ) : null}
      </Sheet>
    </Screen>
  );
}
