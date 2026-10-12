import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from api.main import app
from api.db import Base, get_db
from api.auth import get_password_hash
from api.models import User, UserRole, Organization

SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

@pytest.fixture(autouse=True)
def setup_db():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    org = Organization(name="TestOrg", slug="testorg")
    db.add(org)
    db.commit()
    db.refresh(org)
    admin = User(email="admin@test.com", hashed_password=get_password_hash("pass123")[:72],
                 full_name="Admin", role=UserRole.admin, org_id=org.id)
    editor = User(email="editor@test.com", hashed_password=get_password_hash("pass123")[:72],
                  full_name="Editor", role=UserRole.editor, org_id=org.id)
    db.add_all([admin, editor])
    db.commit()
    yield
    Base.metadata.drop_all(bind=engine)

@pytest.fixture
def client():
    return TestClient(app)

def test_health(client):
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"

def test_login(client):
    r = client.post("/auth/login", params={"email": "admin@test.com", "password": "pass123"})
    assert r.status_code == 200
    assert "access_token" in r.json()

def test_login_bad(client):
    r = client.post("/auth/login", params={"email": "admin@test.com", "password": "wrong"})
    assert r.status_code == 401

def test_me(client):
    token = client.post("/auth/login", params={"email": "admin@test.com", "password": "pass123"}).json()["access_token"]
    r = client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 200
    assert r.json()["email"] == "admin@test.com"

def test_brief_crud(client):
    token = client.post("/auth/login", params={"email": "admin@test.com", "password": "pass123"}).json()["access_token"]
    h = {"Authorization": f"Bearer {token}"}
    # create
    r = client.post("/briefs", json={"title": "Test"}, headers=h)
    assert r.status_code == 200
    bid = r.json()["id"]
    # list
    r = client.get("/briefs", headers=h)
    assert len(r.json()) == 1
    # get
    r = client.get(f"/briefs/{bid}", headers=h)
    assert r.json()["title"] == "Test"
    # update
    r = client.patch(f"/briefs/{bid}", json={"script": "Hello world"}, headers=h)
    assert r.json()["script"] == "Hello world"

def test_editor_cannot_approve(client):
    token = client.post("/auth/login", params={"email": "editor@test.com", "password": "pass123"}).json()["access_token"]
    h = {"Authorization": f"Bearer {token}"}
    r = client.post("/briefs", json={"title": "X"}, headers=h)
    bid = r.json()["id"]
    r = client.post(f"/briefs/{bid}/approve", headers=h)
    assert r.status_code == 403

def test_unauthorized(client):
    r = client.get("/briefs")
    assert r.status_code == 401
