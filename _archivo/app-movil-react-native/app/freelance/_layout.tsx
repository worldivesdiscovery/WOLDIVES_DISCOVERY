import { Tabs } from 'expo-router';
import React from 'react';
import { FREELANCE } from '@/demo';
import { useApp } from '@/store';
import { tabIcon, tabOptions } from '@/tabs';

export default function FreelanceTabs() {
  const { c, t, offers } = useApp();
  const pending = FREELANCE.offers.filter((o) => !offers[o.id]).length;
  return (
    <Tabs screenOptions={tabOptions(c)}>
      <Tabs.Screen name="hoy" options={{ title: t('Hoy'), tabBarIcon: tabIcon(c, 'sun') }} />
      <Tabs.Screen name="agenda" options={{ title: t('Agenda'), tabBarIcon: tabIcon(c, 'calendar') }} />
      <Tabs.Screen name="trabajos" options={{ title: t('Trabajos'), tabBarIcon: tabIcon(c, 'briefcase'), tabBarBadge: pending || undefined, tabBarBadgeStyle: { backgroundColor: c.accent, color: c.onAccent } }} />
      <Tabs.Screen name="cobros" options={{ title: t('Cobros'), tabBarIcon: tabIcon(c, 'wallet') }} />
    </Tabs>
  );
}
