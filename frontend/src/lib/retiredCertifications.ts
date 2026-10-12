// Aviso de certificaciones retiradas por su proveedor (39.24/39.25). El
// contenido del track lo rehace S2; esto solo pone el aviso en la interfaz
// mientras ese trabajo no esté. Lista fija y corta a propósito: no hay campo
// `retired` en el esquema de tracks.json (CLAUDE.md: name_es/name_en/order/
// color/icon, nunca otra forma) y content/** no es terreno de esta sesión.
export interface RetiredCertification {
  code: string;
  replacement: string;
}

export const RETIRED_CERTIFICATIONS: Record<string, RetiredCertification> = {
  track43: { code: 'MLA-C01', replacement: 'MLA-C02' },
  // track45 ya no: su contenido es AI-901 (el examen nuevo), así que el aviso
  // «examen retirado» que mostraba sobre él era falso (2026-10-12).
};

export function retiredCertificationFor(trackId: string): RetiredCertification | undefined {
  return RETIRED_CERTIFICATIONS[trackId];
}
