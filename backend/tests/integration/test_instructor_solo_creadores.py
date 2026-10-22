"""28.3: el panel de instructor es solo para creadores, también en el backend.

Antes la guarda era solo de cliente: cualquier sesión que llamara a
`/instructor/analytics` o `/instructor/profile` se convertía en instructor
(`get_or_create_instructor`). Ahora sin `can_create_courses` y sin perfil previo
es 403 y no se crea nada.
"""

from __future__ import annotations

import pytest
from sqlalchemy import func, select

from app.models.instructor import Instructor

BASE = "/api/v1/instructor"


@pytest.mark.asyncio
@pytest.mark.parametrize("path", ["/analytics", "/payouts", "/profile", "/courses"])
async def test_a_regular_user_is_refused_and_no_instructor_is_created(
    client, db_session, user, auth_headers, path
) -> None:
    assert user.can_create_courses is False
    r = await client.get(BASE + path, headers=auth_headers)
    assert r.status_code == 403, r.text
    count = await db_session.scalar(select(func.count(Instructor.id)).where(Instructor.user_id == user.id))
    assert count == 0


@pytest.mark.asyncio
async def test_an_admin_gets_the_panel(client, db_session, user, auth_headers) -> None:
    user.is_admin = True
    db_session.add(user)
    await db_session.commit()
    r = await client.get(BASE + "/analytics", headers=auth_headers)
    assert r.status_code == 200, r.text
