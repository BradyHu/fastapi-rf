import pytest
from fastapi.testclient import TestClient

from main import app


@pytest.fixture(scope='function')
def client():
    with TestClient(app) as c:
        yield c


@pytest.fixture(scope='function')
def user(client):
    response = client.post('/user/account/register/', json={
        "username": 'username',
        "nickname": "nickname",
        "password": "password"
    })
    return response


@pytest.fixture()
def user_token(client, user):
    token = client.post('/user/account/token/', data={
        'username': "username",
        'password': "password"
    }).json()['access_token']
    return token


@pytest.fixture(scope='function')
def user2(client):
    response = client.post('/user/account/register/', json={
        "username": 'username2',
        "nickname": "nickname2",
        "password": "password2"
    })
    return response


@pytest.fixture()
def user2_token(client, user2):
    token = client.post('/user/account/token/', data={
        'username': "username2",
        'password': "password2"
    }).json()['access_token']
    return token
