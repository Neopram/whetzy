---
title: "Normas de la comunidad y cómo reportar"
last_updated: "2026-10-02"
effective_date: "pendiente de publicar"
language: "es"
status: "BORRADOR — pendiente de revisión profesional (H.20) y de que el dueño confirme el contacto de soporte"
version: "1.0.0"
---

# Normas de la comunidad y cómo reportar

**BORRADOR — no publicado.** Ningún usuario ve este texto todavía; no está cargado por
ninguna clave i18n ni ruta de la app. Se escribe para cubrir el mínimo que exige Apple App
Store Review Guideline **1.2 / 1.2.1** (contenido generado por el usuario): al menos uno de
filtro de contenido objetable, mecanismo de reporte, capacidad de bloquear, o información de
contacto publicada. Confirmado en `docs/store/app-store-review-checklist.md` (filas 1.2 y
1.2.1, 2026-09-30): hoy no hay ninguno de los cuatro.

## 1. A qué se aplica

El nombre de usuario (`username`) y el nombre visible (`display_name`) que cada persona elige
al registrarse son el único texto que otro usuario puede ver hoy en Whetzy: en los retos de
duelo (te reta por `username`, aparece en la notificación "X te retó a un duelo") y en las
tablas de ligas. Whetzy no tiene foros, comentarios, mensajes ni contenido que un usuario
publique para que otros lo lean — estas normas cubren solo el nombre elegido.

## 2. Qué no está permitido en un nombre de usuario o nombre visible

- Insultos, lenguaje de odio o acoso dirigido a una persona o grupo.
- Suplantación de otra persona, de Whetzy o de su equipo.
- Contenido sexual explícito, violento o ilegal.
- Información de contacto de terceros sin su permiso.

## 3. Cómo reportar un nombre de usuario

Si ves un nombre de usuario o nombre visible que incumple lo anterior, escribe a
**[CONTACTO DE SOPORTE PENDIENTE DE CONFIRMAR — hoy `support@whetzy.com` aparece en
`docs/legal/dpa.es.md` §12, pero nadie ha confirmado que sea el buzón que se publicará para
esto]** con el nombre de usuario exacto y, si puedes, una captura. Lo revisamos y, si
corresponde, cambiamos o retiramos el nombre.

**Esto es hoy un proceso manual.** No existe todavía un botón de "reportar" dentro de la app
ni un endpoint que lo automatice — es trabajo de ingeniería pendiente (ledger 19.11, fuera de
mi terreno: `backend/app/api/v1/endpoints/duels.py` y `admin.py`). Este texto no afirma que
ese botón exista.

## 4. Bloquear a otro usuario

Hoy la app **no tiene** una función para bloquear a otro usuario. Si quieres evitar que
alguien concreto te rete a un duelo, escribe al mismo contacto de soporte del punto 3 y lo
gestionamos manualmente mientras no exista la función en la app.

## 5. Qué hacemos con un reporte

Revisamos el nombre reportado contra las normas del punto 2. Si lo incumple, lo sustituimos
por un nombre genérico y avisamos a la cuenta correspondiente por correo. Reincidencia
repetida puede llevar a la suspensión de la cuenta.

---

**Estado**: BORRADOR, no publicado. Pendiente: (a) que el dueño confirme el buzón de
contacto; (b) revisión profesional (H.20); (c) que ingeniería (S1) decida si esto vive en
`frontend/src/i18n/{es,en}/legal.json` como página propia o dentro de los Términos
publicados, y si construye el endpoint de reportar/bloquear que sustituiría el proceso manual
del punto 3.
