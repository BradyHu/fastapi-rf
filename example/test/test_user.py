from fastapi.testclient import TestClient


def test_user_register(client: TestClient):
    response = client.post('/user/account/register/', json={
        "username": 'username',
        "nickname": "nickname",
        "password": "password"
    })
    assert response.status_code == 200


def test_user_login(client: TestClient, user):
    response = client.post('/user/account/token/', data={
        'username': 'username',
        'password': 'password'
    })
    assert response.status_code == 200


def test_user_sms_login(client: TestClient):
    response = client.post("/user/sms/code/", json={
        'mobile': "mobile",
        'action': 'login'
    }).json()
    response2 = client.post('/user/sms/login/', data={
        'mobile': "mobile",
        'code': response['code']
    })
    assert response2.status_code == 200

# def test_user_info
