"""create the user, apartment and review tables

Revision ID: a52abc977036
Revises:
Create Date: 2026-11-28 02:18:00.206582

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel


# revision identifiers, used by Alembic.
revision: str = "a52abc977036"
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # A database from before Alembic already has these tables (the app used to
    # create them itself when it started): leave it as it is.
    if sa.inspect(op.get_bind()).has_table("review"):
        return
    op.create_table(
        "apartment",
        sa.Column("uid", sa.Uuid(), nullable=False),
        sa.Column(
            "osm_type", sqlmodel.sql.sqltypes.AutoString(length=20), nullable=True
        ),
        sa.Column("osm_id", sa.Integer(), nullable=True),
        sa.Column(
            "osm_class", sqlmodel.sql.sqltypes.AutoString(length=50), nullable=True
        ),
        sa.Column(
            "street", sqlmodel.sql.sqltypes.AutoString(length=255), nullable=True
        ),
        sa.Column(
            "house_number", sqlmodel.sql.sqltypes.AutoString(length=50), nullable=True
        ),
        sa.Column("city", sqlmodel.sql.sqltypes.AutoString(length=100), nullable=False),
        sa.Column("state", sqlmodel.sql.sqltypes.AutoString(length=100), nullable=True),
        sa.Column(
            "postcode", sqlmodel.sql.sqltypes.AutoString(length=20), nullable=True
        ),
        sa.Column(
            "country", sqlmodel.sql.sqltypes.AutoString(length=100), nullable=False
        ),
        sa.Column(
            "country_code", sqlmodel.sql.sqltypes.AutoString(length=2), nullable=False
        ),
        sa.Column("display_name", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("uid"),
        sa.UniqueConstraint(
            "street",
            "house_number",
            "city",
            "postcode",
            "country_code",
            name="uq_apartment_address",
        ),
    )
    with op.batch_alter_table("apartment", schema=None) as batch_op:
        batch_op.create_index(batch_op.f("ix_apartment_city"), ["city"], unique=False)
        batch_op.create_index(
            batch_op.f("ix_apartment_country_code"), ["country_code"], unique=False
        )
        batch_op.create_index(
            batch_op.f("ix_apartment_postcode"), ["postcode"], unique=False
        )
        batch_op.create_index(
            batch_op.f("ix_apartment_street"), ["street"], unique=False
        )
        batch_op.create_index(batch_op.f("ix_apartment_uid"), ["uid"], unique=False)

    op.create_table(
        "user",
        sa.Column("uid", sa.Uuid(), nullable=False),
        sa.Column("name", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("email", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("google_sub", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("uid"),
    )
    with op.batch_alter_table("user", schema=None) as batch_op:
        batch_op.create_index(batch_op.f("ix_user_email"), ["email"], unique=False)
        batch_op.create_index(
            batch_op.f("ix_user_google_sub"), ["google_sub"], unique=True
        )
        batch_op.create_index(batch_op.f("ix_user_name"), ["name"], unique=False)
        batch_op.create_index(batch_op.f("ix_user_uid"), ["uid"], unique=False)

    op.create_table(
        "review",
        sa.Column("uid", sa.Uuid(), nullable=False),
        sa.Column("apartment_uid", sa.Uuid(), nullable=False),
        sa.Column("user_uid", sa.Uuid(), nullable=False),
        sa.Column("title", sqlmodel.sql.sqltypes.AutoString(length=255), nullable=True),
        sa.Column("content", sqlmodel.sql.sqltypes.AutoString(), nullable=True),
        sa.Column("landlord_rating", sa.Integer(), nullable=True),
        sa.Column("location_rating", sa.Integer(), nullable=True),
        sa.Column("condition_rating", sa.Integer(), nullable=True),
        sa.Column("quietness_rating", sa.Integer(), nullable=True),
        sa.Column(
            "status", sqlmodel.sql.sqltypes.AutoString(length=20), nullable=False
        ),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(
            ["apartment_uid"],
            ["apartment.uid"],
        ),
        sa.ForeignKeyConstraint(
            ["user_uid"],
            ["user.uid"],
        ),
        sa.PrimaryKeyConstraint("uid"),
        sa.UniqueConstraint(
            "apartment_uid", "user_uid", name="uq_review_apartment_user"
        ),
    )
    with op.batch_alter_table("review", schema=None) as batch_op:
        batch_op.create_index("idx_review_apartment", ["apartment_uid"], unique=False)
        batch_op.create_index("idx_review_user", ["user_uid"], unique=False)
        batch_op.create_index(
            batch_op.f("ix_review_apartment_uid"), ["apartment_uid"], unique=False
        )
        batch_op.create_index(batch_op.f("ix_review_uid"), ["uid"], unique=False)
        batch_op.create_index(
            batch_op.f("ix_review_user_uid"), ["user_uid"], unique=False
        )


def downgrade() -> None:
    """Downgrade schema."""
    with op.batch_alter_table("review", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_review_user_uid"))
        batch_op.drop_index(batch_op.f("ix_review_uid"))
        batch_op.drop_index(batch_op.f("ix_review_apartment_uid"))
        batch_op.drop_index("idx_review_user")
        batch_op.drop_index("idx_review_apartment")

    op.drop_table("review")
    with op.batch_alter_table("user", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_user_uid"))
        batch_op.drop_index(batch_op.f("ix_user_name"))
        batch_op.drop_index(batch_op.f("ix_user_google_sub"))
        batch_op.drop_index(batch_op.f("ix_user_email"))

    op.drop_table("user")
    with op.batch_alter_table("apartment", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_apartment_uid"))
        batch_op.drop_index(batch_op.f("ix_apartment_street"))
        batch_op.drop_index(batch_op.f("ix_apartment_postcode"))
        batch_op.drop_index(batch_op.f("ix_apartment_country_code"))
        batch_op.drop_index(batch_op.f("ix_apartment_city"))

    op.drop_table("apartment")
