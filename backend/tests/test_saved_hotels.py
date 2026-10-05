"""All mutation tests use temporary databases; no provider or student data."""

import sqlite3
from copy import deepcopy

import pytest
from fastapi.testclient import TestClient

from backend.controllers.database import DatabaseController
from backend.main import app, get_database


def payload(place_id="001:Provider/ID +Case ", zip_code="02108"):
    return {
        "hotel": {"place_id": place_id, "name": "Example Hotel", "formatted_address": "API address", "latitude": 42.36, "longitude": -71.06},
        "search_center": {"requested_zip": zip_code, "resolved_postcode": zip_code, "city": "Boston", "state": "MA", "latitude": 42.357, "longitude": -71.065},
    }


@pytest.fixture
def local(tmp_path):
    database = DatabaseController(tmp_path / "local.sqlite3")
    database.initialize()
    with database.open() as connection:
        original = {
            table: [tuple(row) for row in connection.execute(f"SELECT * FROM {table} ORDER BY 1")]
            for table in ("hotels", "users", "trips", "bookings", "metadata")
        }
    app.dependency_overrides[get_database] = lambda: database
    try:
        with TestClient(app) as client:
            yield client, database
        with database.open() as connection:
            for table, rows in original.items():
                assert [tuple(row) for row in connection.execute(f"SELECT * FROM {table} ORDER BY 1")] == rows
            assert not connection.execute("PRAGMA foreign_key_check").fetchall()
    finally:
        app.dependency_overrides.clear()


def test_save_context_defaults_repeat_and_reopen(local):
    client, database = local
    request = payload()
    assert client.get('/api/saved-hotels', params={'zip': '02108'}).json() == {'search_center': None, 'hotels': []}
    response = client.post('/api/saved-hotels', json=request)
    assert response.status_code == 200
    hotel = response.json()['hotel']
    assert hotel['place_id'] == request['hotel']['place_id']
    assert hotel['demo_nights'] == [
        {'stay_date': f'2026-10-{day}', 'nightly_rate_cents': 10000, 'rooms_available': 20}
        for day in range(10, 15)
    ]
    with database.open() as connection:
        connection.execute('UPDATE demo_hotel_nights SET nightly_rate_cents = 12345, rooms_available = 7 WHERE stay_date = ?', ('2026-10-10',))
    assert client.post('/api/saved-hotels', json=request).status_code == 200
    second_zip = deepcopy(request)
    second_zip['search_center'].update(requested_zip='02109', resolved_postcode='02109')
    assert client.post('/api/saved-hotels', json=second_zip).status_code == 200
    reopened = DatabaseController(database.path)
    reopened.initialize()
    app.dependency_overrides[get_database] = lambda: reopened
    result = client.get('/api/saved-hotels', params={'zip': '02108'}).json()
    assert result['search_center'] == request['search_center']
    assert len(result['hotels']) == 1
    assert result['hotels'][0]['demo_nights'][0]['nightly_rate_cents'] == 12345
    assert result['hotels'][0]['demo_nights'][0]['rooms_available'] == 7
    with database.open() as connection:
        for table, count in [('saved_hotels', 1), ('saved_hotel_locations', 2), ('demo_hotel_nights', 5)]:
            assert connection.execute(f'SELECT COUNT(*) FROM {table}').fetchone()[0] == count
    assert client.get('/api/saved-hotels', params={'zip': '2108'}).status_code == 422
    assert client.get('/api/saved-hotels/status', params=[('place_id', request['hotel']['place_id']), ('place_id', 'unknown')]).json() == {'saved_ids': [request['hotel']['place_id']]}


def test_remove_all_contexts_and_nights_preserves_other_hotels(local):
    client, database = local
    for request in [payload('first', '02108'), payload('first', '02109'), payload('other', '02108')]:
        assert client.post('/api/saved-hotels', json=request).status_code == 200
    assert client.delete('/api/saved-hotels', params={'place_id': 'first'}).json() == {'place_id': 'first', 'removed': True}
    with database.open() as connection:
        for table in ['saved_hotels', 'saved_hotel_locations', 'demo_hotel_nights']:
            assert connection.execute(f'SELECT COUNT(*) FROM {table} WHERE hotel_id = ?', ('first',)).fetchone()[0] == 0
        assert connection.execute('SELECT COUNT(*) FROM demo_hotel_nights WHERE hotel_id = ?', ('other',)).fetchone()[0] == 5
    assert [hotel['place_id'] for hotel in client.get('/api/saved-hotels', params={'zip': '02108'}).json()['hotels']] == ['other']
    assert client.get('/api/saved-hotels', params={'zip': '02109'}).json()['hotels'] == []
    assert client.delete('/api/saved-hotels', params={'place_id': 'first'}).status_code == 404


def test_save_and_remove_roll_back_entire_transaction(local):
    client, database = local
    with database.open() as connection:
        connection.execute("CREATE TRIGGER fail_night BEFORE INSERT ON demo_hotel_nights BEGIN SELECT RAISE(ABORT, 'test failure'); END")
    response = client.post('/api/saved-hotels', json=payload('first'))
    assert response.status_code == 503
    assert 'test failure' not in response.text
    with database.open() as connection:
        for table in ['saved_hotels', 'saved_hotel_locations', 'demo_hotel_nights']:
            assert connection.execute(f'SELECT COUNT(*) FROM {table}').fetchone()[0] == 0
        connection.execute('DROP TRIGGER fail_night')
    assert client.post('/api/saved-hotels', json=payload('first')).status_code == 200
    with database.open() as connection:
        connection.execute("CREATE TRIGGER fail_remove BEFORE DELETE ON saved_hotels BEGIN SELECT RAISE(ABORT, 'test failure'); END")
    assert client.delete('/api/saved-hotels', params={'place_id': 'first'}).status_code == 503
    with database.open() as connection:
        for table, count in [('saved_hotels', 1), ('saved_hotel_locations', 1), ('demo_hotel_nights', 5)]:
            assert connection.execute(f'SELECT COUNT(*) FROM {table}').fetchone()[0] == count


@pytest.mark.parametrize('name', [None, '', 'Name unavailable'])
def test_missing_name_and_address_are_stored_as_null(local, name):
    client, database = local
    request = payload()
    request['hotel'].update(name=name, formatted_address=None)
    assert client.post('/api/saved-hotels', json=request).status_code == 200
    with database.open() as connection:
        row = connection.execute('SELECT name, address FROM saved_hotels').fetchone()
        assert tuple(row) == (None, None)


@pytest.mark.parametrize('change', [
    {'place_id': 123}, {'latitude': 91}, {'longitude': -181},
    {'latitude': True}, {'nightly_rate_cents': 1},
])
def test_invalid_or_client_invented_hotel_fields_rejected(local, change):
    client, _ = local
    request = payload()
    request['hotel'].update(change)
    assert client.post('/api/saved-hotels', json=request).status_code == 422
    assert client.get('/api/saved-hotels', params={'zip': '02108'}).json()['hotels'] == []


def test_mismatched_zip_context_rejected(local):
    client, _ = local
    request = payload()
    request['search_center']['resolved_postcode'] = '02109'
    assert client.post('/api/saved-hotels', json=request).status_code == 422


def test_local_storage_failure_has_safe_feedback(local, monkeypatch):
    client, database = local
    def fail(_):
        raise sqlite3.OperationalError('raw secret-like test error')
    monkeypatch.setattr(database, 'get_saved_hotels', fail)
    response = client.get('/api/saved-hotels', params={'zip': '02108'})
    assert response.status_code == 503
    assert response.json() == {'detail': 'Local hotel storage is unavailable. Try again later.'}
    assert 'raw secret' not in response.text
