ALICE = {"X-User-Id": "alice"}
BOB = {"X-User-Id": "bob"}


def make_folder(client, name, parent_id=None, headers=ALICE):
    return client.post("/folders", json={"name": name, "parent_id": parent_id}, headers=headers)


def test_create_folder_at_root(client):
    r = make_folder(client, "Projects")
    assert r.status_code == 201
    body = r.json()
    assert body["name"] == "Projects"
    assert body["type"] == "folder"
    assert body["parent_id"] is None


def test_duplicate_name_in_same_folder_is_rejected(client):
    make_folder(client, "Projects")
    assert make_folder(client, "Projects").status_code == 409


def test_same_name_allowed_in_different_folders(client):
    a = make_folder(client, "A").json()["id"]
    b = make_folder(client, "B").json()["id"]
    assert make_folder(client, "Notes", parent_id=a).status_code == 201
    assert make_folder(client, "Notes", parent_id=b).status_code == 201


def test_create_under_missing_parent_returns_404(client):
    r = make_folder(client, "Orphan", parent_id="does-not-exist")
    assert r.status_code == 404


def test_parent_must_be_a_folder(client):
    upload = client.post(
        "/files", files={"file": ("a.txt", b"x", "text/plain")}, headers=ALICE
    ).json()
    r = make_folder(client, "Child", parent_id=upload["id"])
    assert r.status_code == 400


def test_invalid_name_rejected(client):
    assert make_folder(client, "a/b").status_code == 422
    assert make_folder(client, "   ").status_code == 422


def test_list_root_shows_folders_before_files(client):
    make_folder(client, "Zeta")
    make_folder(client, "Alpha")
    client.post("/files", files={"file": ("note.txt", b"hi", "text/plain")}, headers=ALICE)
    names = [n["name"] for n in client.get("/nodes", headers=ALICE).json()]
    assert names == ["Alpha", "Zeta", "note.txt"]


def test_other_users_cannot_see_or_list_folder(client):
    folder_id = make_folder(client, "Private").json()["id"]
    assert client.get(f"/nodes/{folder_id}", headers=BOB).status_code == 404
    assert client.get("/nodes", headers=BOB).json() == []


def test_missing_identity_header_is_rejected(client):
    assert client.get("/nodes").status_code == 422
    assert client.get("/nodes", headers={"X-User-Id": "  "}).status_code == 401
