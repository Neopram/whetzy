export interface Domain { domain_id: string; name_es: string; name_en: string; weight_pct: number; p_known_mean: number; skills_assessed: number; skills_total: number; ready: boolean }
export interface Readiness { track_id: string; domains: Domain[] }
export const readiness: Readiness = { track_id: 'track09', domains: [
{ domain_id: 'dom0901', name_es: 'Fundamentos de Python', name_en: 'Computer programming and Python fundamentals', weight_pct: 18, p_known_mean: 0.71, skills_assessed: 4, skills_total: 5, ready: false },
{ domain_id: 'dom0902', name_es: 'Flujo de control y funciones', name_en: 'Control flow', weight_pct: 29, p_known_mean: 0.82, skills_assessed: 3, skills_total: 3, ready: true },
{ domain_id: 'dom0903', name_es: 'Estructuras de datos y módulos', name_en: 'Data collections', weight_pct: 25, p_known_mean: 0.48, skills_assessed: 3, skills_total: 5, ready: false },
{ domain_id: 'dom0904', name_es: 'Funciones y excepciones', name_en: 'Functions and exceptions', weight_pct: 28, p_known_mean: 0.30, skills_assessed: 1, skills_total: 2, ready: false },
] };
export const readinessScore = Math.round(100 * readiness.domains.reduce((sum, domain) => sum + domain.weight_pct * domain.p_known_mean, 0) / readiness.domains.reduce((sum, domain) => sum + domain.weight_pct, 0));
