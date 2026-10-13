// Bottom navigation, the same for the three sides of the app. Android: Material 3 bar with the pill behind the
// active icon. iOS: floating translucent bar (system blur).
import { BlurView } from 'expo-blur';
import { Tabs } from 'expo-router';
import React from 'react';
import { ColorValue, StyleSheet, View } from 'react-native';
import { Icon, IconName } from './icons';
import { Palette } from './theme';
import { isIOS } from './ui';

type ScreenOptions = NonNullable<React.ComponentProps<typeof Tabs>['screenOptions']>;

export function tabOptions(c: Palette): ScreenOptions {
  return {
    headerShown: false,
    tabBarActiveTintColor: c.text,
    tabBarInactiveTintColor: c.muted,
    tabBarLabelStyle: { fontSize: 12, fontWeight: '700' },
    tabBarStyle: isIOS
      ? { position: 'absolute', left: 16, right: 16, bottom: 20, height: 66, borderRadius: 33, borderTopWidth: 0, backgroundColor: 'transparent', overflow: 'hidden', paddingBottom: 8 }
      : { backgroundColor: c.dark ? '#0B2234' : '#E3EEF2', borderTopWidth: 0, height: 82, paddingTop: 8, paddingBottom: 12, elevation: 0 },
    tabBarBackground: isIOS ? () => <BlurView intensity={60} tint={c.dark ? 'dark' : 'light'} style={StyleSheet.absoluteFill} /> : undefined,
    sceneStyle: { backgroundColor: c.bg },
  };
}

export function tabIcon(c: Palette, name: IconName) {
  return ({ focused, color }: { focused: boolean; color: ColorValue }) => (
    <View style={{ width: isIOS ? 40 : 58, height: 30, borderRadius: 15, alignItems: 'center', justifyContent: 'center', backgroundColor: focused && !isIOS ? c.accent : 'transparent' }}>
      <Icon name={name} size={22} color={focused && !isIOS ? c.onAccent : (color as string)} />
    </View>
  );
}
