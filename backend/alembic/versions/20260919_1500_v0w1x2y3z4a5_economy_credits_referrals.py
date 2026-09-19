"""Economia: ledger de creditos por lotes, referidos y codigos promocionales.

Sustituye las tres tablas que `u1v2w3x4y5z6` habia creado para el panel de
admin (`credit_ledger`, `referrals`, `promo_codes`) por el diseno de la serie
29, que es el que se queda: lotes FIFO con caducidad, clave de idempotencia y
el saldo derivado de sumar el ledger en vez de guardado en `balance_after`
—un saldo almacenado se desincroniza en cuanto falla una escritura, y este
ledger es inmutable justamente para que no pueda pasar.

Las tres se recrean en vez de alterarse porque la clave primaria de
`credit_ledger` cambia de UUID a entero: los lotes se referencian entre si
(`lot_id`) y con UUID el FIFO no tiene orden natural. **Antes de tocar nada se
comprueba que esten vacias**; si alguna tiene filas, la migracion se planta y
no borra nada. En el momento de escribirla el unico escritor de `credit_ledger`
era el webhook de Paddle, que todavia no existe como cuenta.

Revision ID: v0w1x2y3z4a5
Revises: u2v3w4x5y6z7
Create Date: 2026-09-19 15:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


revision = 'v0w1x2y3z4a5'
# Iba colgada de 't9u0v1w2x3y4', la misma que 'u2v3w4x5y6z7', lo que dejaba dos
# cabezas y hacia fallar `alembic upgrade head` — y con el deploy automatico
# desde master, eso es el arranque de produccion.
down_revision = 'u2v3w4x5y6z7'
branch_labels = None
depends_on = None


REPLACED = ('credit_ledger', 'referrals', 'promo_codes')


def _assert_empty() -> None:
    """Se niega a continuar si alguna de las tablas que sustituye tiene datos."""
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    existing = set(inspector.get_table_names())
    for table in REPLACED:
        if table not in existing:
            continue
        rows = bind.execute(sa.text(f'SELECT count(*) FROM {table}')).scalar_one()
        if rows:
            raise RuntimeError(
                f"'{table}' tiene {rows} fila(s) y esta migracion la recrea con otra "
                f"clave primaria. No la borro yo: exporta esas filas, decide como "
                f"convertirlas al ledger por lotes y vuelve a lanzarla."
            )


def upgrade() -> None:
    _assert_empty()
    for table in REPLACED:
        op.drop_table(table, if_exists=True)

    op.create_table(
        'credit_ledger',
        # Identity y no BigInteger a secas: sin ella el INSERT no tiene de donde
        # sacar el id y revienta por NOT NULL.
        sa.Column('id', sa.BigInteger(), sa.Identity(always=False), nullable=False),
        sa.Column('user_id', sa.UUID(), nullable=False),
        sa.Column('amount', sa.Integer(), nullable=False),
        sa.Column('reason', sa.String(length=50), nullable=False),
        sa.Column('ref_type', sa.String(length=50), nullable=True),
        sa.Column('ref_id', sa.String(length=255), nullable=True),
        sa.Column('lot_id', sa.BigInteger(), nullable=True),
        sa.Column('idempotency_key', sa.String(length=255), nullable=False),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint('amount != 0', name='ck_credit_nonzero'),
        sa.ForeignKeyConstraint(['lot_id'], ['credit_ledger.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        # La unicidad de `idempotency_key` ya la da esta restriccion: la version
        # anterior creaba ademas un indice con ESE MISMO nombre, y Postgres
        # rechaza el segundo objeto por nombre repetido.
        sa.UniqueConstraint('idempotency_key', name='uq_idempotency_key'),
    )
    op.create_index('ix_credit_ledger_user_id', 'credit_ledger', ['user_id'], unique=False)
    op.create_index('ix_credit_user_created', 'credit_ledger', ['user_id', 'created_at'], unique=False)
    op.create_index('ix_credit_expires', 'credit_ledger', ['expires_at'], unique=False)
    op.create_index('ix_credit_ledger_created_at', 'credit_ledger', ['created_at'], unique=False)

    op.create_table(
        'referral_codes',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('user_id', sa.UUID(), nullable=False),
        sa.Column('code', sa.String(length=10), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('code', name='uq_referral_code'),
        sa.UniqueConstraint('user_id', name='uq_referral_user'),
    )
    op.create_index('ix_referral_codes_code', 'referral_codes', ['code'], unique=False)

    op.create_table(
        'referrals',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('referrer_id', sa.UUID(), nullable=False),
        sa.Column('referred_id', sa.UUID(), nullable=False),
        sa.Column('status', sa.String(length=50), nullable=False, server_default='pending'),
        sa.Column('activated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['referrer_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['referred_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        # Un invitado solo puede serlo una vez, venga de quien venga: es el
        # limite que impide cobrar el bono creando cuentas en bucle.
        sa.UniqueConstraint('referred_id', name='uq_referred_once'),
    )
    op.create_index('ix_referrals_referrer_id', 'referrals', ['referrer_id'], unique=False)
    op.create_index('ix_referrals_status', 'referrals', ['status'], unique=False)

    op.create_table(
        'promo_codes',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('code', sa.String(length=10), nullable=False),
        sa.Column('code_type', sa.String(length=50), nullable=False),
        sa.Column('credits', sa.Integer(), nullable=False),
        sa.Column('max_uses', sa.Integer(), nullable=True),
        sa.Column('current_uses', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('max_per_user', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('language', sa.String(length=2), nullable=True),
        sa.Column('campaign_id', sa.String(length=100), nullable=True),
        sa.Column('created_by', sa.String(length=50), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('code', name='uq_promo_code'),
    )
    op.create_index('ix_promo_codes_campaign', 'promo_codes', ['campaign_id'], unique=False)

    op.create_table(
        'promo_code_redemptions',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('user_id', sa.UUID(), nullable=False),
        sa.Column('promo_code_id', sa.UUID(), nullable=False),
        sa.Column('credit_ledger_id', sa.BigInteger(), nullable=False),
        sa.Column('redeemed_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['credit_ledger_id'], ['credit_ledger.id'], ),
        sa.ForeignKeyConstraint(['promo_code_id'], ['promo_codes.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id', 'promo_code_id', name='uq_user_promo'),
    )
    op.create_index('ix_promo_code_redemptions_user', 'promo_code_redemptions', ['user_id'], unique=False)

    op.create_table(
        'credit_expense_caps',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('user_id', sa.UUID(), nullable=False),
        sa.Column('monthly_learning_cap', sa.Integer(), nullable=False, server_default='1500'),
        sa.Column('monthly_learning_earned', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('monthly_referral_cap', sa.Integer(), nullable=False, server_default='10'),
        sa.Column('monthly_referral_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('cap_reset_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('last_activation_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id', name='uq_caps_user'),
    )


def downgrade() -> None:
    # Vuelve a dejar las tres tablas del panel de admin tal y como las creo
    # `u1v2w3x4y5z6`, para que bajar de revision no deje el esquema a medias.
    for table in ('credit_expense_caps', 'promo_code_redemptions', 'promo_codes',
                  'referrals', 'referral_codes', 'credit_ledger'):
        op.drop_table(table, if_exists=True)

    op.create_table(
        'credit_ledger',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('user_id', sa.UUID(), nullable=False),
        sa.Column('amount', sa.Integer(), nullable=False),
        sa.Column('reason', sa.String(length=128), nullable=False),
        sa.Column('reference_id', sa.String(length=255), nullable=True),
        sa.Column('balance_after', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_credit_ledger_user_id', 'credit_ledger', ['user_id'], unique=False)
    op.create_index('ix_credit_ledger_created_at', 'credit_ledger', ['created_at'], unique=False)

    op.create_table(
        'referrals',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('referrer_id', sa.UUID(), nullable=False),
        sa.Column('referred_id', sa.UUID(), nullable=False),
        sa.Column('status', sa.String(length=32), nullable=False, server_default='pending'),
        sa.Column('reward_credits', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['referrer_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['referred_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_referrals_referrer_id', 'referrals', ['referrer_id'], unique=False)
    op.create_index('ix_referrals_referred_id', 'referrals', ['referred_id'], unique=False)
    op.create_index('ix_referrals_status', 'referrals', ['status'], unique=False)

    op.create_table(
        'promo_codes',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('code', sa.String(length=32), nullable=False),
        sa.Column('referrer_id', sa.UUID(), nullable=True),
        sa.Column('discount_percent', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('max_uses', sa.Integer(), nullable=True),
        sa.Column('current_uses', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['referrer_id'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('code'),
    )
    op.create_index('ix_promo_codes_code', 'promo_codes', ['code'], unique=False)
