from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from shodh.models.organization import Organization
from shodh.models.membership import Membership, MembershipRole

from shodh.repositories.organization_repository import (
    get_organization_by_id,
    get_membership,
    list_user_organizations,
    list_organization_members,
    count_organizers
)

from shodh.repositories.user_repository import get_user_by_email

from shodh.schemas.organization import (
    OrganizationCreateRequest,
    AddOrganizationMemberRequest,
    UpdateMemberRoleRequest
)


def create_organization(
    db: Session,
    payload: OrganizationCreateRequest,
    current_user_id: UUID
) -> Organization:

    organization = Organization(
        name=payload.name,
        slug=payload.slug
    )

    try:
        db.add(organization)
        db.flush()

        # Creator automatically becomes an organizer.
        membership = Membership(
            organization_id=organization.id,
            user_id=current_user_id,
            role=MembershipRole.ORGANIZER
        )

        db.add(membership)

        # Organization and creator membership commit together.
        db.commit()
        db.refresh(organization)

        return organization

    except IntegrityError as exc:
        db.rollback()

        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Organization slug already exists"
        ) from exc


def get_user_organizations(
    db: Session,
    user_id: UUID
):

    results = list_user_organizations(db, user_id)

    return [
        {
            "id": organization.id,
            "name": organization.name,
            "slug": organization.slug,
            "created_at": organization.created_at,
            "role": role
        }
        for organization, role in results
    ]


def get_organization(
    db: Session,
    organization_id: UUID
) -> Organization:

    organization = get_organization_by_id(
        db,
        organization_id
    )

    if organization is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Organization not found"
        )

    return organization


def add_organization_member(
    db: Session,
    organization_id: UUID,
    payload: AddOrganizationMemberRequest
) -> Membership:

    user = get_user_by_email(db, str(payload.email).lower())

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    existing_membership = get_membership(
        db,
        organization_id,
        user.id
    )

    if existing_membership is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="User is already a member of this organization"
        )

    membership = Membership(
        organization_id=organization_id,
        user_id=user.id,
        role=payload.role,
        user=user
    )

    try:
        db.add(membership)
        db.commit()
        db.refresh(membership)

        return membership

    except IntegrityError as exc:
        db.rollback()

        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Membership already exists or could not be created"
        ) from exc


def get_organization_members(
    db: Session,
    organization_id: UUID
):

    return list_organization_members(
        db,
        organization_id
    )


def update_member_role(
    db: Session,
    organization_id: UUID,
    user_id: UUID,
    payload: UpdateMemberRoleRequest
) -> Membership:

    # Lock the parent organization row to serialize role changes
    # affecting its organizer count across independent processes.
    organization = get_organization_by_id(
        db,
        organization_id,
        for_update=True
    )

    if organization is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Organization not found"
        )

    membership = get_membership(
        db,
        organization_id,
        user_id
    )

    if membership is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Membership not found"
        )

    if membership.role == payload.role:
        return membership

    # Never leave an organization without an organizer.
    if (
        membership.role == MembershipRole.ORGANIZER
        and payload.role == MembershipRole.PARTICIPANT
    ):

        organizer_count = count_organizers(
            db,
            organization_id
        )

        if organizer_count <= 1:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Organization must have at least one organizer"
            )

    membership.role = payload.role

    db.commit()
    db.refresh(membership)

    return membership