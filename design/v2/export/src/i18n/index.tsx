import { createContext, useContext, useEffect, useState, type ReactNode } from 'react';
import { es } from './es';
import { en } from './en';
import { me } from '../fixtures/me';
export type Language = 'es' | 'en';
export type Theme = 'dark' | 'light';
type Key = keyof typeof es;
interface Settings { language: Language; theme: Theme; setLanguage: (language: Language) => void; setTheme: (theme: Theme) => void; t: (key: Key) => string; pick: (item: { name_es: string; name_en: string }) => string }
const Context = createContext<Settings | null>(null);
export function SettingsProvider({ children }: { children: ReactNode }) {
 const [language, setLanguage] = useState<Language>(me.language);
 const [theme, setTheme] = useState<Theme>('dark');
 useEffect(() => { document.documentElement.dataset.theme = theme; }, [theme]);
 useEffect(() => { document.documentElement.lang = language; }, [language]);
 const t = (key: Key) => language === 'es' ? es[key] : en[key];
 const pick = (item: { name_es: string; name_en: string }) => language === 'es' ? item.name_es : item.name_en;
 return <Context.Provider value={{ language, theme, setLanguage, setTheme, t, pick }}>{children}</Context.Provider>;
}
export function useSettings() { const value = useContext(Context); if (!value) throw new Error('SettingsProvider missing'); return value; }
