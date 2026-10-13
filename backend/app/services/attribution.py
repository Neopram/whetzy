"""Origen de un alta (D-23 del dueño, 2026-10-12): mínimo y sin terceros.

El cliente manda lo que vio al llegar (los `utm_*` de la URL y si traía un
enlace de referido); aquí se clasifica, para que la regla viva en un solo
sitio y no en cada versión del frontend.
"""

from __future__ import annotations

# utm_medium que usan las plataformas de anuncios para el tráfico de pago.
_PAID_MEDIUMS = frozenset({"cpc", "ppc", "paid", "paidsocial", "paid_social", "display", "ads"})


def classify(
    *,
    utm_source: str | None,
    utm_medium: str | None,
    utm_campaign: str | None,
    referred: bool,
) -> tuple[str, str | None]:
    """Devuelve (`signup_source`, `signup_campaign`).

    `signup_source` es uno de: referral, paid, utm, direct. El referido manda
    sobre los utm: lo trajo una persona, no un anuncio.
    """
    campaign = (utm_campaign or utm_source or "").strip()[:64] or None
    if referred:
        return "referral", None
    if (utm_medium or "").strip().lower() in _PAID_MEDIUMS:
        return "paid", campaign
    if campaign:
        return "utm", campaign
    return "direct", None
