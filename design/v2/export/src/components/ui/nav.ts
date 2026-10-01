import { House, Layers3, Target, Trophy, UserRound } from 'lucide-react';
export const navItems = [
 { to: '/hoy', key: 'today', icon: House },
 { to: '/rutas', key: 'tracks', icon: Layers3 },
 { to: '/practicar', key: 'practice', icon: Target },
 { to: '/ranking', key: 'ranking', icon: Trophy },
 { to: '/yo', key: 'profile', icon: UserRound },
] as const;
