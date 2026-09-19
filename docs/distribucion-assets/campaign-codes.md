# Campaign Codes & Video Attribution — 24.13 / 26.0 / 27.0

## Overview

Each of the 6 video pieces (3 formats × 2 languages) has a unique campaign code embedded in the final seconds (super) and in the description/metadata. These codes tie viewing analytics to sign-up attribution.

## Campaign Code Format

```
YT-[LANGUAGE]-[FORMAT]

YT    = YouTube channel marker
[LANGUAGE]  = ES | EN
[FORMAT]    = PROD (producto) | MOTOR (motor) | SHORT (corto)
```

## Video Index

| Format | Lang | Code | Duration | File | Series |
|--------|------|------|----------|------|--------|
| Producto | ES | `YT-ES-PROD` | 2 min | `whetzy-product-es.mp4` | 26.0 |
| Producto | EN | `YT-EN-PROD` | 2 min | `whetzy-product-en.mp4` | 27.0 |
| Motor | ES | `YT-ES-MOTOR` | 5 min | `whetzy-motor-es.mp4` | 26.0 |
| Motor | EN | `YT-EN-MOTOR` | 5 min | `whetzy-motor-en.mp4` | 27.0 |
| Short | ES | `YT-ES-SHORT` | 60s | `whetzy-short-es.mp4` | 26.0 |
| Short | EN | `YT-EN-SHORT` | 60s | `whetzy-short-en.mp4` | 27.0 |

## Integration with 29.4 (Referral System)

When a user signs up via `?ref=YT-ES-PROD`:
1. Frontend captures URL param via `useSearchParams()` in `AuthScreen`
2. Sends to `/auth/register` payload: `"referral_code": "YT-ES-PROD"`
3. Backend creates `UserReferral` entry linking user → campaign code
4. Admin panel (22.1) shows: `Referrals: {YT-ES-PROD: 142, YT-EN-PROD: 89, ...}`

## Super Placement (1:30-1:45 before end)

Each video shows code in final seconds:
```
whetzy.com
YT-XX-YYYY
```

White text, 44pt font, 3s hold at end, fade to black.

## Description Template (YouTube/TikTok)

```
Aprende Python adaptativo con Whetzy.
⚡ Gratuito, sin tarjeta
🎯 Adaptado a tu nivel
🏆 Certificado verificable

Empieza: whetzy.com
Código: YT-ES-PROD

---
Chapters (YouTube):
0:00 — Intro
0:15 — Problema
0:35 — Solución
1:20 — CTA
```

## Analytics & ROI (Admin 22.1)

Monthly cohort report: **Referrals by code**
```
YT-ES-PROD   142 signups   68 retained (D7)   12 converted
YT-ES-MOTOR  89 signups    41 retained (D7)   5 converted
YT-ES-SHORT  256 signups   110 retained (D7)  22 converted
...
```

K-factor (viral coefficient) = referrals from code / total conversions.

## Rendering Checklist

- [ ] All 6 scripts approved by owner (26.0 / 27.0)
- [ ] All 6 videos rendered 1080p H.264
- [ ] Campaign codes hard-coded in final super (1:30-1:45)
- [ ] YouTube descriptions with code + whetzy.com
- [ ] TikTok descriptions optimized for 150-char limit
- [ ] Subtitles: Auto-generated + manual QA
- [ ] Metadata: Title, thumbnail, tags per SEO checklist
- [ ] Upload scheduling: Stagger to 3/week (no flood)
