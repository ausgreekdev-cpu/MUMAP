import uuid
import re
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..database import get_db
from ..models.user import User
from ..utils import utcnow
from ..models.organization import Organization, OrgMember, OrgInvite, OrgRole, ORG_ROLE_HIERARCHY, PLAN_DEFAULTS
from ..schemas.organization import (
    OrganizationCreate, OrganizationUpdate, OrganizationResponse,
    OrgMemberResponse, OrgInviteCreate, OrgInviteResponse,
)
from ..services.auth import get_current_user

router = APIRouter(prefix="/orgs", tags=["organizations"])


def slugify(name: str) -> str:
    slug = name.lower().strip()
    slug = re.sub(r"[^\w\s-]", "", slug)
    slug = re.sub(r"[\s_]+", "-", slug)
    slug = re.sub(r"-+", "-", slug)
    return slug.strip("-")


def get_org_member(org_id: int, user_id: int, db: Session) -> OrgMember:
    return db.query(OrgMember).filter(
        OrgMember.org_id == org_id,
        OrgMember.user_id == user_id,
    ).first()


def require_org_role(min_role: OrgRole, org_id: int, user: User, db: Session) -> OrgMember:
    membership = get_org_member(org_id, user.id, db)
    if not membership:
        raise HTTPException(status_code=404, detail="Not a member of this organization")
    if ORG_ROLE_HIERARCHY[OrgRole(membership.role)] < ORG_ROLE_HIERARCHY[min_role]:
        raise HTTPException(status_code=403, detail=f"Requires {min_role.value} role or higher")
    return membership


@router.post("/", response_model=OrganizationResponse)
def create_organization(
    data: OrganizationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    base_slug = slugify(data.name)
    slug = base_slug
    counter = 1
    while db.query(Organization).filter(Organization.slug == slug).first():
        slug = f"{base_slug}-{counter}"
        counter += 1

    defaults = PLAN_DEFAULTS["free"]
    org = Organization(
        name=data.name,
        slug=slug,
        description=data.description,
        plan="free",
        max_agents=defaults["max_agents"],
        max_members=defaults["max_members"],
        monthly_token_limit=defaults["monthly_token_limit"],
        monthly_task_limit=defaults["monthly_task_limit"],
    )
    db.add(org)
    db.flush()

    owner = OrgMember(
        org_id=org.id,
        user_id=current_user.id,
        role=OrgRole.OWNER,
        invited_by=current_user.id,
    )
    db.add(owner)
    db.commit()
    db.refresh(org)

    return OrganizationResponse(
        id=org.id,
        name=org.name,
        slug=org.slug,
        description=org.description,
        logo_url=org.logo_url,
        plan=org.plan,
        max_agents=org.max_agents,
        max_members=org.max_members,
        monthly_token_limit=org.monthly_token_limit,
        monthly_task_limit=org.monthly_task_limit,
        settings=org.settings or {},
        is_active=org.is_active,
        member_count=1,
        created_at=org.created_at,
        updated_at=org.updated_at,
    )


@router.get("/", response_model=list[OrganizationResponse])
def list_organizations(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    memberships = db.query(OrgMember).filter(OrgMember.user_id == current_user.id).all()
    result = []
    for m in memberships:
        org = m.organization
        member_count = db.query(OrgMember).filter(OrgMember.org_id == org.id).count()
        result.append(OrganizationResponse(
            id=org.id,
            name=org.name,
            slug=org.slug,
            description=org.description,
            logo_url=org.logo_url,
            plan=org.plan,
            max_agents=org.max_agents,
            max_members=org.max_members,
            monthly_token_limit=org.monthly_token_limit,
            monthly_task_limit=org.monthly_task_limit,
            settings=org.settings or {},
            is_active=org.is_active,
            member_count=member_count,
            created_at=org.created_at,
            updated_at=org.updated_at,
        ))
    return result


@router.get("/{org_id}", response_model=OrganizationResponse)
def get_organization(
    org_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    require_org_role(OrgRole.VIEWER, org_id, current_user, db)
    org = db.query(Organization).filter(Organization.id == org_id).first()
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")

    member_count = db.query(OrgMember).filter(OrgMember.org_id == org.id).count()
    return OrganizationResponse(
        id=org.id,
        name=org.name,
        slug=org.slug,
        description=org.description,
        logo_url=org.logo_url,
        plan=org.plan,
        max_agents=org.max_agents,
        max_members=org.max_members,
        monthly_token_limit=org.monthly_token_limit,
        monthly_task_limit=org.monthly_task_limit,
        settings=org.settings or {},
        is_active=org.is_active,
        member_count=member_count,
        created_at=org.created_at,
        updated_at=org.updated_at,
    )


@router.put("/{org_id}", response_model=OrganizationResponse)
def update_organization(
    org_id: int,
    data: OrganizationUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    require_org_role(OrgRole.ADMIN, org_id, current_user, db)
    org = db.query(Organization).filter(Organization.id == org_id).first()
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")

    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(org, key, value)

    db.commit()
    db.refresh(org)

    member_count = db.query(OrgMember).filter(OrgMember.org_id == org.id).count()
    return OrganizationResponse(
        id=org.id,
        name=org.name,
        slug=org.slug,
        description=org.description,
        logo_url=org.logo_url,
        plan=org.plan,
        max_agents=org.max_agents,
        max_members=org.max_members,
        monthly_token_limit=org.monthly_token_limit,
        monthly_task_limit=org.monthly_task_limit,
        settings=org.settings or {},
        is_active=org.is_active,
        member_count=member_count,
        created_at=org.created_at,
        updated_at=org.updated_at,
    )


@router.delete("/{org_id}")
def delete_organization(
    org_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    require_org_role(OrgRole.OWNER, org_id, current_user, db)
    org = db.query(Organization).filter(Organization.id == org_id).first()
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")

    db.delete(org)
    db.commit()

    return {"message": "Organization deleted"}


@router.post("/{org_id}/members/invite", response_model=OrgInviteResponse)
def invite_member(
    org_id: int,
    data: OrgInviteCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    require_org_role(OrgRole.ADMIN, org_id, current_user, db)
    org = db.query(Organization).filter(Organization.id == org_id).first()
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")

    existing_member = db.query(OrgMember).join(User).filter(
        OrgMember.org_id == org_id,
        User.email == data.email,
    ).first()
    if existing_member:
        raise HTTPException(status_code=400, detail="User is already a member")

    if data.role not in [r.value for r in OrgRole]:
        raise HTTPException(status_code=400, detail="Invalid role")

    if org.max_members != -1:
        current_count = db.query(OrgMember).filter(OrgMember.org_id == org_id).count()
        if current_count >= org.max_members:
            raise HTTPException(status_code=400, detail="Organization member limit reached")

    token = uuid.uuid4().hex
    expires_at = utcnow() + timedelta(days=7)

    invite = OrgInvite(
        org_id=org_id,
        email=data.email,
        role=data.role,
        token=token,
        invited_by=current_user.id,
        expires_at=expires_at,
    )
    db.add(invite)
    db.commit()
    db.refresh(invite)

    return OrgInviteResponse(
        id=invite.id,
        email=invite.email,
        role=invite.role,
        expires_at=invite.expires_at,
        accepted_at=invite.accepted_at,
    )


@router.post("/{org_id}/members/accept", response_model=OrgMemberResponse)
def accept_invite(
    org_id: int,
    token: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    invite = db.query(OrgInvite).filter(
        OrgInvite.org_id == org_id,
        OrgInvite.token == token,
    ).first()
    if not invite:
        raise HTTPException(status_code=404, detail="Invite not found")

    if invite.accepted_at is not None:
        raise HTTPException(status_code=400, detail="Invite already accepted")

    if invite.expires_at < utcnow():
        raise HTTPException(status_code=400, detail="Invite has expired")

    if invite.email != current_user.email:
        raise HTTPException(status_code=403, detail="Invite is not for this user")

    existing = get_org_member(org_id, current_user.id, db)
    if existing:
        raise HTTPException(status_code=400, detail="Already a member of this organization")

    invite.accepted_at = utcnow()

    membership = OrgMember(
        org_id=org_id,
        user_id=current_user.id,
        role=invite.role,
        invited_by=invite.invited_by,
    )
    db.add(membership)
    db.commit()
    db.refresh(membership)

    user = db.query(User).filter(User.id == current_user.id).first()
    return OrgMemberResponse(
        user_id=user.id,
        username=user.username,
        email=user.email,
        role=membership.role,
        joined_at=membership.joined_at,
    )


@router.get("/{org_id}/members", response_model=list[OrgMemberResponse])
def list_members(
    org_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    require_org_role(OrgRole.VIEWER, org_id, current_user, db)
    members = db.query(OrgMember).filter(OrgMember.org_id == org_id).all()
    result = []
    for m in members:
        user = db.query(User).filter(User.id == m.user_id).first()
        if user:
            result.append(OrgMemberResponse(
                user_id=user.id,
                username=user.username,
                email=user.email,
                role=m.role,
                joined_at=m.joined_at,
            ))
    return result


@router.put("/{org_id}/members/{user_id}/role", response_model=OrgMemberResponse)
def change_member_role(
    org_id: int,
    user_id: int,
    role: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    require_org_role(OrgRole.OWNER, org_id, current_user, db)

    if role not in [r.value for r in OrgRole]:
        raise HTTPException(status_code=400, detail="Invalid role")

    membership = get_org_member(org_id, user_id, db)
    if not membership:
        raise HTTPException(status_code=404, detail="Member not found")

    if membership.role == OrgRole.OWNER and role != OrgRole.OWNER:
        owners = db.query(OrgMember).filter(
            OrgMember.org_id == org_id,
            OrgMember.role == OrgRole.OWNER,
        ).count()
        if owners <= 1:
            raise HTTPException(status_code=400, detail="Cannot remove the last owner")

    membership.role = role
    db.commit()
    db.refresh(membership)

    user = db.query(User).filter(User.id == user_id).first()
    return OrgMemberResponse(
        user_id=user.id,
        username=user.username,
        email=user.email,
        role=membership.role,
        joined_at=membership.joined_at,
    )


@router.delete("/{org_id}/members/{user_id}")
def remove_member(
    org_id: int,
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    require_org_role(OrgRole.ADMIN, org_id, current_user, db)

    membership = get_org_member(org_id, user_id, db)
    if not membership:
        raise HTTPException(status_code=404, detail="Member not found")

    if membership.role == OrgRole.OWNER and current_user.id != user_id:
        raise HTTPException(status_code=403, detail="Cannot remove an owner")

    if current_user.id == user_id:
        raise HTTPException(status_code=400, detail="Cannot remove yourself")

    db.delete(membership)
    db.commit()

    return {"message": "Member removed"}
