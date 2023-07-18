from fastapi.testclient import TestClient


def test_organization_list(client: TestClient, user_token, user2_token):
    resp = client.get('/organization/organizations/', headers={
        'Authorization': f"Bearer {user_token}"
    })
    assert resp.status_code == 200
    assert resp.json()['total'] == 1


def test_organization_current_organization(client, user_token):
    resp = client.get('/organization/organizations/current_organization/', headers={
        'Authorization': f"Bearer {user_token}"
    })
    assert resp.status_code == 200
    assert resp.json()['name'] == 'nickname'
