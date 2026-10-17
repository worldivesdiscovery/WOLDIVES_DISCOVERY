import { Tabs } from 'expo-router';
import React from 'react';
import { useApp } from '@/store';
import { tabIcon, tabOptions } from '@/tabs';

export default function CentreTabs() {
  const { c, t } = useApp();
  return (
    <Tabs screenOptions={tabOptions(c)}>
      <Tabs.Screen name="hoy" options={{ title: t('Hoy'), tabBarIcon: tabIcon(c, 'sun') }} />
      <Tabs.Screen name="agenda" options={{ title: t('Agenda'), tabBarIcon: tabIcon(c, 'calendar') }} />
      <Tabs.Screen name="clientes" options={{ title: t('Clientes'), tabBarIcon: tabIcon(c, 'users') }} />
      <Tabs.Screen name="mas" options={{ title: t('Más'), tabBarIcon: tabIcon(c, 'more') }} />
    </Tabs>
  );
}
