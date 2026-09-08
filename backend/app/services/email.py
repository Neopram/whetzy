"""Transactional email service for Whetzy.

Provider hierarchy:
  1. SMTP (gmail, SES, etc.) — configured via SMTP_* env vars
  2. Resend HTTP API — configured via RESEND_API_KEY
  3. Log fallback — always available; used in dev and when provider fails

Select provider with EMAIL_PROVIDER=smtp|resend|log.
If the selected provider raises, the exception is caught and the email is
logged (best-effort transactional). The caller always succeeds.
"""

from __future__ import annotations

import logging
import smtplib
import ssl
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

logger = logging.getLogger("whetzy.email")

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
}


def _render(template_name: str, lang: str, **kwargs: str) -> tuple[str, str]:
    """Return (subject, html_body) for template + language."""
    lang_key = lang if lang in ("es", "en") else "es"
    tpl = _TEMPLATES[template_name][lang_key]
    subject = tpl["subject"].format(**kwargs)
    html = tpl["html"].format(**kwargs)
    return subject, html


# ── Providers ─────────────────────────────────────────────────────────────────


def _send_smtp(to: str, subject: str, html: str) -> None:
    from app.core.config import settings

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = f"{settings.EMAIL_FROM_NAME} <{settings.EMAIL_FROM_ADDRESS}>"
    msg["To"] = to
    msg.attach(MIMEText(html, "html", "utf-8"))

    context = ssl.create_default_context()
    with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=10) as smtp:
        if settings.SMTP_USE_TLS:
            smtp.starttls(context=context)
        if settings.SMTP_USER:
            smtp.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
        smtp.sendmail(settings.EMAIL_FROM_ADDRESS, to, msg.as_string())


def _send_resend(to: str, subject: str, html: str) -> None:
    import urllib.request
    import json as _json

    from app.core.config import settings

    payload = _json.dumps({
        "from": f"{settings.EMAIL_FROM_NAME} <{settings.EMAIL_FROM_ADDRESS}>",
        "to": [to],
        "subject": subject,
        "html": html,
    }).encode()
    req = urllib.request.Request(
        "https://api.resend.com/emails",
        data=payload,
        headers={
            "Authorization": f"Bearer {settings.RESEND_API_KEY}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=10) as resp:
        if resp.status >= 400:
            raise RuntimeError(f"Resend API error {resp.status}")


def _send_log(to: str, subject: str, html: str) -> None:
    logger.info(
        "EMAIL (log-only) to=%s subject=%r body_chars=%d",
        to, subject, len(html),
    )


# ── Public API ─────────────────────────────────────────────────────────────────


def _dispatch(to: str, subject: str, html: str) -> None:
    from app.core.config import settings

    provider = settings.EMAIL_PROVIDER
    try:
        if provider == "smtp" and settings.SMTP_USER:
            _send_smtp(to, subject, html)
        elif provider == "resend" and settings.RESEND_API_KEY:
            _send_resend(to, subject, html)
        else:
            _send_log(to, subject, html)
        logger.info("email_sent provider=%s to=%s subject=%r", provider, to, subject)
    except Exception:
        # Best-effort: log and continue so callers always succeed.
        logger.exception("email_failed provider=%s to=%s subject=%r", provider, to, subject)
        _send_log(to, subject, html)


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
