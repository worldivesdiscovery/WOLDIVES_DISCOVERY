import { Tabs } from 'expo-router';
import React from 'react';
import { useApp } from '@/store';
import { tabIcon, tabOptions } from '@/tabs';

export default function DiverTabs() {
  const { c, t } = useApp();
  return (
    <Tabs screenOptions={tabOptions(c)}>
      <Tabs.Screen name="inicio" options={{ title: t('Inicio'), tabBarIcon: tabIcon(c, 'home') }} />
      <Tabs.Screen name="explorar" options={{ title: t('Explorar'), tabBarIcon: tabIcon(c, 'map') }} />
      <Tabs.Screen name="reservas" options={{ title: t('Reservas'), tabBarIcon: tabIcon(c, 'ticket') }} />
      <Tabs.Screen name="perfil" options={{ title: t('Perfil'), tabBarIcon: tabIcon(c, 'user') }} />
    </Tabs>
  );
}
