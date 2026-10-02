"""Transactional email service for Whetzy.

El proveedor se **deduce de las credenciales que haya**, no de una variable
aparte: `RESEND_API_KEY` -> Resend, si no `SMTP_USER`+`SMTP_PASSWORD` -> SMTP,
y si no hay nada, `log`. `EMAIL_PROVIDER` solo sirve para forzar uno.

Antes hacian falta dos variables correctas a la vez (`EMAIL_PROVIDER=resend`
**y** la clave) y acertar una sola no bastaba: el envio caia al log sin decir
nada. Con `EMAIL_PROVIDER` valiendo `smtp` por defecto y `SMTP_USER` vacio, eso
es lo que pasaba en produccion — `POST /auth/forgot-password` devolvia 200, la
pantalla decia «te hemos enviado un enlace» y no salia nada de la maquina. Quien
olvidaba su contrasena perdia la cuenta (ledger H.30).

Un envio sigue sin poder tumbar la peticion que lo dispara —no se le puede decir
a quien pide un reset si su correo existe, ni hacerle esperar a un SMTP lento—,
pero ahora **un fallo se ve**: marcador `email_not_configured` en cada envio
perdido, y `POST /admin/email/test` para comprobarlo de verdad sin adivinar.

El envio es bloqueante (smtplib, HTTP) y estas funciones se llaman desde
endpoints async, asi que se despacha en un hilo: antes, un SMTP con 10 s de
timeout congelaba el bucle de eventos entero.
"""

from __future__ import annotations

import asyncio
import logging
import smtplib
import ssl
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

logger = logging.getLogger("whetzy.email")

# Los envios en segundo plano se guardan aqui mientras corren: una tarea de
# asyncio sin referencia viva puede recogerla el GC a media ejecucion.
_en_vuelo: set[asyncio.Task[None]] = set()

# ── Templates ─────────────────────────────────────────────────────────────────

_TEMPLATES: dict[str, dict[str, dict[str, str]]] = {
    "welcome": {
        "es": {
            "subject": "Bienvenido/a a Whetzy, {name}!",
            "html": """\
<h2>Hola, {name}!</h2>
<p>Tu cuenta en <strong>Whetzy</strong> está lista.
Empieza a aprender Python para ingeniería de datos ahora.</p>
<p><a href="{base_url}" style="background:#6366f1;color:#fff;padding:10px 20px;
border-radius:6px;text-decoration:none;">Ir a Whetzy</a></p>
<p>Si no creaste esta cuenta, ignora este correo.</p>""",
        },
        "en": {
            "subject": "Welcome to Whetzy, {name}!",
            "html": """\
<h2>Hi, {name}!</h2>
<p>Your <strong>Whetzy</strong> account is ready.
Start learning Python for data engineering right now.</p>
<p><a href="{base_url}" style="background:#6366f1;color:#fff;padding:10px 20px;
border-radius:6px;text-decoration:none;">Go to Whetzy</a></p>
<p>If you didn't create this account, ignore this email.</p>""",
        },
    },
    "email_verification": {
        "es": {
            "subject": "Verifica tu email en Whetzy",
            "html": """\
<h2>Hola, {name}!</h2>
<p>Verifica tu dirección de email haciendo clic en el botón de abajo.
El enlace expira en <strong>24 horas</strong>.</p>
<p><a href="{verify_url}" style="background:#6366f1;color:#fff;padding:10px 20px;
border-radius:6px;text-decoration:none;">Verificar email</a></p>
<p>O copia este enlace en tu navegador:<br>{verify_url}</p>
<p>Si no creaste esta cuenta, ignora este correo.</p>""",
        },
        "en": {
            "subject": "Verify your Whetzy email",
            "html": """\
<h2>Hi, {name}!</h2>
<p>Verify your email address by clicking the button below.
The link expires in <strong>24 hours</strong>.</p>
<p><a href="{verify_url}" style="background:#6366f1;color:#fff;padding:10px 20px;
border-radius:6px;text-decoration:none;">Verify email</a></p>
<p>Or copy this link into your browser:<br>{verify_url}</p>
<p>If you didn't create this account, ignore this email.</p>""",
        },
    },
    "password_reset": {
        "es": {
            "subject": "Restablece tu contraseña de Whetzy",
            "html": """\
<h2>Hola, {name}!</h2>
<p>Recibimos una solicitud para restablecer tu contraseña.
El enlace expira en <strong>1 hora</strong> y solo puede usarse una vez.</p>
<p><a href="{reset_url}" style="background:#6366f1;color:#fff;padding:10px 20px;
border-radius:6px;text-decoration:none;">Restablecer contraseña</a></p>
<p>O copia este enlace en tu navegador:<br>{reset_url}</p>
<p>Si no solicitaste este cambio, ignora este correo. Tu contraseña no cambiará.</p>""",
        },
        "en": {
            "subject": "Reset your Whetzy password",
            "html": """\
<h2>Hi, {name}!</h2>
<p>We received a request to reset your password.
The link expires in <strong>1 hour</strong> and can only be used once.</p>
<p><a href="{reset_url}" style="background:#6366f1;color:#fff;padding:10px 20px;
border-radius:6px;text-decoration:none;">Reset password</a></p>
<p>Or copy this link into your browser:<br>{reset_url}</p>
<p>If you didn't request this, ignore this email. Your password won't change.</p>""",
        },
    },
    "support_ticket": {
        "es": {
            "subject": "Tu ticket de soporte #{ticket_id} en Whetzy",
            "html": """\
<h2>Hola, {name}!</h2>
<p>Recibimos tu solicitud de soporte (#{ticket_id}).</p>
<p><strong>Asunto:</strong> {subject}</p>
<p>Nuestro equipo revisará tu consulta dentro de 24 horas y te responderemos pronto.</p>
<p>Gracias por usar <strong>Whetzy</strong>.</p>""",
        },
        "en": {
            "subject": "Your Whetzy support ticket #{ticket_id}",
            "html": """\
<h2>Hi, {name}!</h2>
<p>We received your support request (#{ticket_id}).</p>
<p><strong>Subject:</strong> {subject}</p>
<p>Our team will review your inquiry within 24 hours and get back to you soon.</p>
<p>Thank you for using <strong>Whetzy</strong>.</p>""",
        },
    },
    "reactivation": {
        "es": {
            "subject": "Te extrañamos en Whetzy, {name} — tienes un regalo",
            "html": """\
<h2>Hola, {name}!</h2>
<p>Hace un tiempo que no practicas en <strong>Whetzy</strong>. Sabemos que la
constancia es lo más difícil, así que te dejamos un código con créditos gratis
para que retomes sin excusas:</p>
<p style="text-align:center;font-size:24px;font-weight:bold;
letter-spacing:2px;color:#6366f1;">{code}</p>
<p>El código vale <strong>{credits} créditos</strong> y expira en <strong>72 horas</strong>. Canjéalo en Yo → Cartera → Código promocional.</p>
<p><a href="{base_url}" style="background:#6366f1;color:#fff;padding:10px 20px;
border-radius:6px;text-decoration:none;">Volver a Whetzy</a></p>
<p style="font-size:12px;color:#888;">¿No quieres más correos como este? <a href="{unsubscribe_url}">Darte de baja</a> con un clic.</p>""",
        },
        "en": {
            "subject": "We miss you at Whetzy, {name} — here's a gift",
            "html": """\
<h2>Hi, {name}!</h2>
<p>It's been a while since you practiced on <strong>Whetzy</strong>. We know
consistency is the hardest part, so here's a free credit code to help you
get back on track:</p>
<p style="text-align:center;font-size:24px;font-weight:bold;
letter-spacing:2px;color:#6366f1;">{code}</p>
<p>The code is worth <strong>{credits} credits</strong> and expires in <strong>72 hours</strong>. Redeem it in You → Wallet → Promo code.</p>
<p><a href="{base_url}" style="background:#6366f1;color:#fff;padding:10px 20px;
border-radius:6px;text-decoration:none;">Back to Whetzy</a></p>
<p style="font-size:12px;color:#888;">Don't want emails like this? <a href="{unsubscribe_url}">Unsubscribe</a> in one click.</p>""",
        },
    },
    "credit_expiry": {
        "es": {
            "subject": "{name}, {credits} créditos de Whetzy caducan el {expiry_date}",
            "html": """\
<h2>Hola, {name}!</h2>
<p>El <strong>{expiry_date}</strong> caducan <strong>{credits} créditos</strong> de tu
cartera de Whetzy. Los créditos caducan a los 90 días de ganarlos.</p>
<p>Puedes gastarlos antes en Yo → Cartera.</p>
<p><a href="{base_url}" style="background:#6366f1;color:#fff;padding:10px 20px;
border-radius:6px;text-decoration:none;">Ir a Whetzy</a></p>
<p style="font-size:12px;color:#888;">¿No quieres más correos como este? <a href="{unsubscribe_url}">Darte de baja</a> con un clic.</p>""",
        },
        "en": {
            "subject": "{name}, {credits} Whetzy credits expire on {expiry_date}",
            "html": """\
<h2>Hi, {name}!</h2>
<p>On <strong>{expiry_date}</strong>, <strong>{credits} credits</strong> in your Whetzy
wallet expire. Credits expire 90 days after you earn them.</p>
<p>You can spend them before then in You → Wallet.</p>
<p><a href="{base_url}" style="background:#6366f1;color:#fff;padding:10px 20px;
border-radius:6px;text-decoration:none;">Go to Whetzy</a></p>
<p style="font-size:12px;color:#888;">Don't want emails like this? <a href="{unsubscribe_url}">Unsubscribe</a> in one click.</p>""",
        },
    },
    "renewal_reminder": {
        "es": {
            "subject": "Tu suscripción Whetzy se renueva el {renewal_date}",
            "html": """\
<h2>Hola, {name}!</h2>
<p>Tu suscripción <strong>{plan_name}</strong> se renovará automáticamente
el <strong>{renewal_date}</strong> por <strong>{amount}</strong>.</p>
<p>Si deseas cancelar la renovación automática, puedes hacerlo desde
Yo → Cancelar suscripción en la app antes de esa fecha. Conservas el acceso
hasta el final del periodo pagado.</p>
<p>Gracias por seguir aprendiendo con <strong>Whetzy</strong>.</p>
<p style="font-size:12px;color:#888;">Si tienes preguntas sobre tu suscripción,
contacta a support@whetzy.com</p>""",
        },
        "en": {
            "subject": "Your Whetzy subscription renews on {renewal_date}",
            "html": """\
<h2>Hi, {name}!</h2>
<p>Your <strong>{plan_name}</strong> subscription will automatically renew
on <strong>{renewal_date}</strong> for <strong>{amount}</strong>.</p>
<p>If you wish to cancel automatic renewal, you can do so from
You → Cancel subscription in the app before that date. You keep access
until the end of the paid period.</p>
<p>Thank you for continuing to learn with <strong>Whetzy</strong>.</p>
<p style="font-size:12px;color:#888;">If you have questions about your subscription,
contact support@whetzy.com</p>""",
        },
    },
    "support_resolved": {
        "es": {
            "subject": "Tu ticket de soporte {ticket_id} ha sido resuelto",
            "html": """\
<h2>Hola, {name}!</h2>
<p>Tu ticket de soporte (#{ticket_id}) ha sido marcado como resuelto.</p>
<p><strong>Solución:</strong></p>
<p>{resolution}</p>
<p>Si tienes más preguntas, responde a este email o contáctanos en soporte@whetzy.com</p>
<p>Gracias por tu paciencia.</p>""",
        },
        "en": {
            "subject": "Your support ticket {ticket_id} has been resolved",
            "html": """\
<h2>Hi, {name}!</h2>
<p>Your support ticket (#{ticket_id}) has been marked as resolved.</p>
<p><strong>Resolution:</strong></p>
<p>{resolution}</p>
<p>If you have further questions, reply to this email or contact us at support@whetzy.com</p>
<p>Thank you for your patience.</p>""",
        },
    },
}


def _render(template_name: str, lang: str, **kwargs: str) -> tuple[str, str]:
    """Return (subject, html_body) for template + language."""
    lang_key = lang if lang in ("es", "en") else "es"
    tpl = _TEMPLATES[template_name][lang_key]
    subject = tpl["subject"].format(**kwargs)
    html = tpl["html"].format(**kwargs)
    return subject, html


# ── Providers ─────────────────────────────────────────────────────────────────


def _unsubscribe_headers(unsubscribe_url: str | None) -> dict[str, str]:
    """Cabeceras de baja. Solo un correo de marketing lleva enlace https y
    «One-Click» (RFC 8058, el que piden Gmail y Yahoo); el resto, el mailto de
    siempre. Antes todos anunciaban One-Click con un mailto, que el RFC no admite."""
    from app.core.config import settings

    mailto = f"<mailto:{settings.EMAIL_FROM_ADDRESS}?subject=unsubscribe>"
    if unsubscribe_url is None:
        return {"List-Unsubscribe": mailto}
    return {
        "List-Unsubscribe": f"<{unsubscribe_url}>, {mailto}",
        "List-Unsubscribe-Post": "List-Unsubscribe=One-Click",
    }


def _send_smtp(to: str, subject: str, html: str, unsubscribe_url: str | None = None) -> None:
    from app.core.config import settings

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = f"{settings.EMAIL_FROM_NAME} <{settings.EMAIL_FROM_ADDRESS}>"
    msg["To"] = to
    for name, value in _unsubscribe_headers(unsubscribe_url).items():
        msg[name] = value
    msg.attach(MIMEText(html, "html", "utf-8"))

    context = ssl.create_default_context()
    with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=10) as smtp:
        if settings.SMTP_USE_TLS:
            smtp.starttls(context=context)
        if settings.SMTP_USER:
            smtp.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
        smtp.sendmail(settings.EMAIL_FROM_ADDRESS, to, msg.as_string())


def _send_resend(to: str, subject: str, html: str, unsubscribe_url: str | None = None) -> None:
    """Envia por la API de Resend.

    Con `urllib` el `if resp.status >= 400` era codigo muerto —`urlopen` ya lanza
    en 4xx— y el motivo real (clave invalida, remitente sin verificar) se perdia.
    `httpx` deja leer el cuerpo, que es donde Resend explica que pasa.
    """
    import httpx

    from app.core.config import settings

    resp = httpx.post(
        "https://api.resend.com/emails",
        json={
            "from": f"{settings.EMAIL_FROM_NAME} <{settings.EMAIL_FROM_ADDRESS}>",
            "to": [to],
            "subject": subject,
            "html": html,
            "headers": _unsubscribe_headers(unsubscribe_url),
        },
        headers={"Authorization": f"Bearer {settings.RESEND_API_KEY}"},
        timeout=10.0,
    )
    if resp.status_code >= 400:
        raise RuntimeError(f"Resend {resp.status_code}: {resp.text[:400]}")


def _send_log(to: str, subject: str, html: str) -> None:
    logger.info(
        "EMAIL (log-only) to=%s subject=%r body_chars=%d",
        to, subject, len(html),
    )


# ── Public API ─────────────────────────────────────────────────────────────────


def resolve_provider() -> str:
    """Proveedor que se usaria ahora mismo: 'resend', 'smtp' o 'log'.

    Se deduce de las credenciales presentes. `EMAIL_PROVIDER` solo fuerza uno, y
    si el forzado no tiene credenciales se dice en voz alta en vez de degradar a
    `log` en silencio — degradar en silencio es justamente lo que dejo a los
    usuarios sin poder recuperar su contrasena.
    """
    from app.core.config import settings

    forzado: str | None = (settings.EMAIL_PROVIDER or "").strip().lower()
    if forzado == "log":
        return "log"
    if forzado in ("", "auto"):
        forzado = None

    tiene = {
        "resend": bool(settings.RESEND_API_KEY),
        "smtp": bool(settings.SMTP_USER and settings.SMTP_PASSWORD),
    }
    if forzado is not None and forzado in tiene:
        if tiene[forzado]:
            return forzado
        logger.warning(
            "EMAIL_PROVIDER=%s pero le faltan credenciales; se buscan otras", forzado
        )
    if tiene["resend"]:
        return "resend"
    if tiene["smtp"]:
        return "smtp"
    return "log"


def is_configured() -> bool:
    """True si un correo saldria de verdad de la maquina."""
    return resolve_provider() != "log"


def describe_config() -> dict[str, object]:
    """Lo que hace falta para responder «llega el correo?» sin adivinar."""
    from app.core.config import settings

    provider = resolve_provider()
    return {
        "provider": provider,
        "configured": provider != "log",
        "forced_by_env": (settings.EMAIL_PROVIDER or "").strip().lower() or None,
        "from": f"{settings.EMAIL_FROM_NAME} <{settings.EMAIL_FROM_ADDRESS}>",
        "frontend_base_url": settings.FRONTEND_BASE_URL,
        "has_resend_key": bool(settings.RESEND_API_KEY),
        "has_smtp_credentials": bool(settings.SMTP_USER and settings.SMTP_PASSWORD),
    }


def _send_now(to: str, subject: str, html: str, unsubscribe_url: str | None = None) -> str:
    """Envia en este hilo y **propaga el fallo**. Devuelve el proveedor usado.

    Es la ruta que usa `POST /admin/email/test`: ahi si se quiere la excepcion
    con el motivo, no un log que hay que ir a buscar.
    """
    provider = resolve_provider()
    # Solo el marketing pasa `unsubscribe_url`: el correo de servicio llama igual
    # que siempre.
    extra = {"unsubscribe_url": unsubscribe_url} if unsubscribe_url else {}
    if provider == "resend":
        _send_resend(to, subject, html, **extra)
    elif provider == "smtp":
        _send_smtp(to, subject, html, **extra)
    else:
        raise RuntimeError(
            "Sin proveedor de correo: define RESEND_API_KEY, o SMTP_USER y "
            "SMTP_PASSWORD, en el entorno del backend"
        )
    return provider


def _entregar(to: str, subject: str, html: str, unsubscribe_url: str | None = None) -> None:
    """Un envio, con el fallo registrado de forma que se pueda encontrar."""
    provider = resolve_provider()
    if provider == "log":
        # Ni excepcion (rompería el registro y el reset) ni silencio: un marcador
        # que se puede grepear en los logs de Railway y que dice que falta.
        logger.error(
            "email_not_configured to=%s subject=%r — no sale de la maquina. "
            "Define RESEND_API_KEY (o SMTP_USER y SMTP_PASSWORD). Ledger H.30",
            to, subject,
        )
        _send_log(to, subject, html)
        return
    try:
        _send_now(to, subject, html, unsubscribe_url)
        logger.info("email_sent provider=%s to=%s subject=%r", provider, to, subject)
    except Exception:
        logger.exception("email_failed provider=%s to=%s subject=%r", provider, to, subject)
        _send_log(to, subject, html)


def _dispatch(to: str, subject: str, html: str, unsubscribe_url: str | None = None) -> None:
    """Despacha sin bloquear al que llama.

    `smtplib` y el POST a Resend son bloqueantes, y todos los que llaman aqui son
    endpoints async: hacerlo en el hilo del bucle congela el servidor entero
    mientras dure el envio (hasta 10 s de timeout). Si hay bucle, va a un hilo.
    """
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        _entregar(to, subject, html, unsubscribe_url)
        return

    tarea = loop.create_task(asyncio.to_thread(_entregar, to, subject, html, unsubscribe_url))
    _en_vuelo.add(tarea)
    tarea.add_done_callback(_en_vuelo.discard)


def send_welcome(to: str, name: str, lang: str = "es") -> None:
    from app.core.config import settings

    subject, html = _render("welcome", lang, name=name, base_url=settings.FRONTEND_BASE_URL)
    _dispatch(to, subject, html)


def send_email_verification(to: str, name: str, token: str, lang: str = "es") -> None:
    from app.core.config import settings

    verify_url = f"{settings.FRONTEND_BASE_URL}/verify-email?token={token}"
    subject, html = _render("email_verification", lang, name=name, verify_url=verify_url)
    _dispatch(to, subject, html)


def send_password_reset(to: str, name: str, token: str, lang: str = "es") -> None:
    from app.core.config import settings

    reset_url = f"{settings.FRONTEND_BASE_URL}/reset-password?token={token}"
    subject, html = _render("password_reset", lang, name=name, reset_url=reset_url)
    _dispatch(to, subject, html)




def send_support_ticket(to: str, name: str, ticket_id: str, subject: str, lang: str = "es") -> None:
    """Send support ticket acknowledgment email."""
    subject_line, html = _render("support_ticket", lang, name=name, ticket_id=ticket_id, subject=subject)
    _dispatch(to, subject_line, html)


def send_support_resolved(to: str, name: str, ticket_id: str, resolution: str, lang: str = "es") -> None:
    """Send support ticket resolution email."""
    subject_line, html = _render("support_resolved", lang, name=name, ticket_id=ticket_id, resolution=resolution)
    _dispatch(to, subject_line, html)


def send_reactivation(
    to: str, name: str, code: str, credits: int, unsubscribe_url: str, lang: str = "es"
) -> None:
    """Marketing: lleva enlace de baja de un clic (cuerpo y cabecera)."""
    from app.core.config import settings

    subject, html = _render(
        "reactivation", lang, name=name, code=code, credits=str(credits),
        base_url=settings.FRONTEND_BASE_URL, unsubscribe_url=unsubscribe_url,
    )
    _dispatch(to, subject, html, unsubscribe_url)


def send_credit_expiry_warning(
    to: str, name: str, credits: int, expiry_date: str, unsubscribe_url: str, lang: str = "es"
) -> None:
    """Aviso 7 días antes de una caducidad ≥ 200 créditos (ECONOMIA §2.4). Es
    una palanca de retención, así que va como marketing: con baja de un clic."""
    from app.core.config import settings

    subject, html = _render(
        "credit_expiry", lang, name=name, credits=str(credits), expiry_date=expiry_date,
        base_url=settings.FRONTEND_BASE_URL, unsubscribe_url=unsubscribe_url,
    )
    _dispatch(to, subject, html, unsubscribe_url)


def send_renewal_reminder(
    to: str, name: str, plan_name: str, renewal_date: str, amount: str, lang: str = "es",
) -> None:
    subject, html = _render(
        "renewal_reminder", lang,
        name=name, plan_name=plan_name, renewal_date=renewal_date, amount=amount,
    )
    _dispatch(to, subject, html)

