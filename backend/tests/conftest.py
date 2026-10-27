import os
os.environ["DATABASE_URL"] = "sqlite:///./test_tradepass.db"
os.environ["SECRET_KEY"] = "test-secret-key-long-enough-for-tests-123456"
os.environ["STORAGE_DIR"] = "./test_storage"
import pytest
from fastapi.testclient import TestClient
from app.database import Base, engine, SessionLocal, get_db
from app.main import app

@pytest.fixture(autouse=True)
def clean_db():
    Base.metadata.drop_all(bind=engine); Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)

@pytest.fixture
def client():
    def override_db():
        db=SessionLocal()
        try: yield db
        finally: db.close()
    app.dependency_overrides[get_db]=override_db
    with TestClient(app) as c: yield c
    app.dependency_overrides.clear()

def register(client, email, company):
    r=client.post('/auth/register',json={"company":{"name":company,"country":"IN","company_type":"exporter"},"user":{"name":"Test User","email":email,"password":"SecurePass123!"}})
    assert r.status_code==201, r.text
    return client.post('/auth/login',json={"email":email,"password":"SecurePass123!"}).json()['access_token']
