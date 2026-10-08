from urllib.parse import unquote

from app.core.config import settings

ALICE = {"X-User-Id": "alice"}
BOB = {"X-User-Id": "bob"}


def upload(client, name="hello.txt", data=b"hello world", parent_id=None, headers=ALICE):
    form = {} if parent_id is None else {"parent_id": parent_id}
    return client.post(
        "/files",
        files={"file": (name, data, "text/plain")},
        data=form,
        headers=headers,
    )


def test_upload_and_download_round_trip(client):
    r = upload(client)
    assert r.status_code == 201
    body = r.json()
    assert body["size_bytes"] == len(b"hello world")
    assert body["content_type"] == "text/plain"

    d = client.get(f"/files/{body['id']}/content", headers=ALICE)
    assert d.status_code == 200
    assert d.content == b"hello world"
    assert d.headers["content-type"].startswith("text/plain")
    assert "hello.txt" in unquote(d.headers["content-disposition"])


def test_upload_into_folder(client):
    folder = client.post("/folders", json={"name": "Docs"}, headers=ALICE).json()
    r = upload(client, parent_id=folder["id"])
    assert r.status_code == 201
    children = client.get(f"/nodes?parent_id={folder['id']}", headers=ALICE).json()
    assert [c["name"] for c in children] == ["hello.txt"]


def test_bytes_are_stored_in_blob_store(client):
    body = upload(client).json()
    assert len(client.blobs.objects) == 1
    assert client.blobs.objects[f"alice/{body['id']}"] == b"hello world"


def test_upload_over_limit_is_rejected_and_nothing_stored(client, monkeypatch):
    monkeypatch.setattr(settings, "max_upload_bytes", 5)
    r = upload(client, data=b"0123456789")
    assert r.status_code == 413
    assert client.blobs.objects == {}


def test_duplicate_file_name_in_same_folder_rejected(client):
    upload(client)
    assert upload(client).status_code == 409


def test_other_user_cannot_download(client):
    file_id = upload(client).json()["id"]
    assert client.get(f"/files/{file_id}/content", headers=BOB).status_code == 404


def test_cannot_download_a_folder_as_file(client):
    folder_id = client.post("/folders", json={"name": "Dir"}, headers=ALICE).json()["id"]
    assert client.get(f"/files/{folder_id}/content", headers=ALICE).status_code == 400


def test_non_ascii_filename_downloads_without_error(client):
    r = upload(client, name="résumé 2026.txt")
    assert r.status_code == 201
    d = client.get(f"/files/{r.json()['id']}/content", headers=ALICE)
    assert d.status_code == 200
    assert "r%C3%A9sum%C3%A9" in d.headers["content-disposition"]
