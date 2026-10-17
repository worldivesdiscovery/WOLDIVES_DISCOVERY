import { Redirect } from 'expo-router';
import React from 'react';
import { useApp } from '@/store';

export default function Index() {
  const { role } = useApp();
  if (role === 'buceador') return <Redirect href="/buceador/inicio" />;
  if (role === 'centro') return <Redirect href="/centro/hoy" />;
  if (role === 'freelance') return <Redirect href="/freelance/hoy" />;
  return <Redirect href="/bienvenida" />;
}
