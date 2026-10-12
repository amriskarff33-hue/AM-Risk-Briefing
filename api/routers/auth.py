from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..db import get_db
from ..auth import get_current_user, create_access_token, verify_password, get_password_hash, require_role
from ..models import User, UserRole, Organization, AuditLog
from ..schemas import Token, UserCreate, UserOut, OrgCreate, OrgOut

router = APIRouter(prefix="/auth", tags=["auth"])

@router.post("/login", response_model=Token)
def login(email: str, password: str, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == email).first()
    if not user or not verify_password(password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    if not user.is_active:
        raise HTTPException(status_code=403, detail="Account disabled")
    user.last_login = __import__("datetime").datetime.utcnow()
    db.commit()
    return {"access_token": create_access_token({"sub": user.id, "role": user.role.value, "org_id": user.org_id})}

@router.post("/register", response_model=UserOut)
def register(data: UserCreate, db: Session = Depends(get_db)):
    if db.query(User).filter(User.email == data.email).first():
        raise HTTPException(status_code=409, detail="Email already registered")
    user = User(email=data.email, hashed_password=get_password_hash(data.password),
                full_name=data.full_name, role=data.role)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

@router.get("/me", response_model=UserOut)
def me(user: User = Depends(get_current_user)):
    return user

@router.post("/orgs", response_model=OrgOut)
def create_org(data: OrgCreate, db: Session = Depends(get_db),
               admin: User = Depends(require_role(UserRole.admin))):
    if db.query(Organization).filter(Organization.slug == data.slug).first():
        raise HTTPException(status_code=409, detail="Slug already exists")
    org = Organization(**data.model_dump())
    db.add(org)
    db.commit()
    db.refresh(org)
    return org

@router.get("/orgs", response_model=list[OrgOut])
def list_orgs(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return db.query(Organization).all()
