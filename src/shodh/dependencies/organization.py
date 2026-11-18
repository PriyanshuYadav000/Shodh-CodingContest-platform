from uuid import UUID

from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session

from shodh.database.session import get_db
from shodh.dependencies.auth import get_current_user
from shodh.models.membership import Membership, MembershipRole
from shodh.models.user import User
from shodh.repositories.organization_repository import get_membership


def get_current_organization_membership(
    organization_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Membership:

    membership = get_membership(
        db,
        organization_id,
        current_user.id
    )

    if membership is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Organization not found"
        )

    return membership


def require_organization_role(*allowed_roles: MembershipRole):

    def role_checker(
        membership: Membership = Depends(
            get_current_organization_membership
        )
    ) -> Membership:

        if membership.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient organization permissions"
            )

        return membership

    return role_checker