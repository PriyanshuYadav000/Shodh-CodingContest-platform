from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session, joinedload

from shodh.models.membership import Membership, MembershipRole
from shodh.models.organization import Organization


def get_organization_by_id(
    db: Session,
    organization_id: UUID,
    for_update: bool = False
):
    statement = select(Organization).where(
        Organization.id == organization_id
    )

    if for_update:
        statement = statement.with_for_update()

    return db.scalar(statement)


def list_user_organizations(
    db: Session,
    user_id: UUID
):
    statement = (
        select(Organization, Membership.role)
        .join(
            Membership,
            Membership.organization_id == Organization.id
        )
        .where(Membership.user_id == user_id)
        .order_by(
            Organization.created_at.desc(),
            Organization.id.asc()
        )
    )

    return db.execute(statement).all()


def get_membership(
    db: Session,
    organization_id: UUID,
    user_id: UUID
):
    return db.get(
        Membership,
        (organization_id, user_id)
    )


def list_organization_members(
    db: Session,
    organization_id: UUID
):
    statement = (
        select(Membership)
        .options(joinedload(Membership.user))
        .where(Membership.organization_id == organization_id)
        .order_by(Membership.created_at.asc(), Membership.user_id.asc())
    )

    return db.scalars(statement).all()


def count_organizers(
    db: Session,
    organization_id: UUID
) -> int:
    statement = select(func.count()).select_from(Membership).where(
        Membership.organization_id == organization_id,
        Membership.role == MembershipRole.ORGANIZER
    )

    return db.scalar(statement) or 0