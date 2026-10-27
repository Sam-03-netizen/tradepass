from .conftest import register

def test_register_login_me(client):
    token=register(client,'one@example.com','Company One')
    r=client.get('/me',headers={'Authorization':f'Bearer {token}'})
    assert r.status_code==200 and r.json()['email']=='one@example.com'

def test_duplicate_email(client):
    register(client,'one@example.com','Company One')
    r=client.post('/auth/register',json={"company":{"name":"Another Co","country":"IN","company_type":"exporter"},"user":{"name":"Test User","email":"one@example.com","password":"SecurePass123!"}})
    assert r.status_code==409

def test_shipments_tenant_isolation_and_company_scoped_reference(client):
    token_a=register(client,'one@example.com','Company One'); token_b=register(client,'two@example.com','Company Two')
    ha={'Authorization':f'Bearer {token_a}'}; hb={'Authorization':f'Bearer {token_b}'}
    body={"reference_number":"SHIP-001","product":"Cotton garments","origin_country":"IN","destination_country":"DE"}
    a=client.post('/shipments/',json=body,headers=ha); assert a.status_code==201, a.text
    b=client.post('/shipments/',json=body,headers=hb); assert b.status_code==201, b.text
    assert len(client.get('/shipments/',headers=ha).json())==1
    assert client.get(f"/shipments/{a.json()['id']}",headers=hb).status_code==404

def test_auth_required(client):
    assert client.get('/shipments/').status_code==401

def test_bad_country_rejected(client):
    token=register(client,'one@example.com','Company One')
    r=client.post('/shipments/',json={"reference_number":"SHIP-001","product":"Cotton garments","origin_country":"IND","destination_country":"DE"},headers={'Authorization':f'Bearer {token}'})
    assert r.status_code==422
