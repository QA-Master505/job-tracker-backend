JOB_PAYLOAD = {
    "company_name": "Acme Corp",
    "job_title": "Software Engineer",
    "applied_date": "2026-01-15",
    "status": "applied",
}

INTERVIEW_PAYLOAD = {
    "interview_type": "phone",
    "interview_date": "2026-01-20",
}


# ── GET /jobs/{id}/interviews ─────────────────────────────────────────────────

def test_list_interviews_empty(client, auth_headers, sample_job):
    # A new job has no interview rounds
    response = client.get(f"/jobs/{sample_job['id']}/interviews", headers=auth_headers)

    assert response.status_code == 200
    assert response.json() == []


def test_list_interviews_returns_created_rounds(client, auth_headers, sample_job):
    # Rounds added to a job appear in the list
    job_id = sample_job["id"]
    client.post(f"/jobs/{job_id}/interviews", json=INTERVIEW_PAYLOAD, headers=auth_headers)
    client.post(f"/jobs/{job_id}/interviews", json={**INTERVIEW_PAYLOAD, "interview_type": "virtual"}, headers=auth_headers)

    response = client.get(f"/jobs/{job_id}/interviews", headers=auth_headers)

    assert response.status_code == 200
    assert len(response.json()) == 2


# ── POST /jobs/{id}/interviews ────────────────────────────────────────────────

def test_create_interview_round_success(client, auth_headers, sample_job):
    # First round is created with round_number=1 and all fields populated
    response = client.post(
        f"/jobs/{sample_job['id']}/interviews",
        json=INTERVIEW_PAYLOAD,
        headers=auth_headers,
    )

    assert response.status_code == 201
    data = response.json()
    assert data["round_number"] == 1
    assert data["interview_type"] == INTERVIEW_PAYLOAD["interview_type"]
    assert "id" in data
    assert "created_at" in data


def test_create_second_round_increments_number(client, auth_headers, sample_job):
    # Second round for the same job automatically gets round_number=2
    job_id = sample_job["id"]
    client.post(f"/jobs/{job_id}/interviews", json=INTERVIEW_PAYLOAD, headers=auth_headers)

    response = client.post(
        f"/jobs/{job_id}/interviews",
        json={**INTERVIEW_PAYLOAD, "interview_type": "virtual"},
        headers=auth_headers,
    )

    assert response.status_code == 201
    assert response.json()["round_number"] == 2


def test_create_interview_round_job_not_found(client, auth_headers):
    # Creating a round for a non-existent job returns 404
    response = client.post(
        "/jobs/99999/interviews",
        json=INTERVIEW_PAYLOAD,
        headers=auth_headers,
    )

    assert response.status_code == 404


# ── PUT /jobs/{id}/interviews/{round_id} ─────────────────────────────────────

def test_update_interview_round_success(client, auth_headers, sample_job):
    # Valid update returns 200 with the changed fields applied
    job_id = sample_job["id"]
    round_ = client.post(
        f"/jobs/{job_id}/interviews", json=INTERVIEW_PAYLOAD, headers=auth_headers
    ).json()

    response = client.put(
        f"/jobs/{job_id}/interviews/{round_['id']}",
        json={"interview_type": "onsite", "notes": "On-site loop"},
        headers=auth_headers,
    )

    assert response.status_code == 200
    data = response.json()
    assert data["interview_type"] == "onsite"
    assert data["notes"] == "On-site loop"


def test_update_interview_round_not_found(client, auth_headers, sample_job):
    # Updating a non-existent round ID returns 404
    response = client.put(
        f"/jobs/{sample_job['id']}/interviews/99999",
        json={"interview_type": "virtual"},
        headers=auth_headers,
    )

    assert response.status_code == 404


# ── DELETE /jobs/{id}/interviews/{round_id} ───────────────────────────────────

def test_delete_interview_round_success(client, auth_headers, sample_job):
    # Owner can delete a round; it no longer appears in the list
    job_id = sample_job["id"]
    round_ = client.post(
        f"/jobs/{job_id}/interviews", json=INTERVIEW_PAYLOAD, headers=auth_headers
    ).json()

    response = client.delete(
        f"/jobs/{job_id}/interviews/{round_['id']}",
        headers=auth_headers,
    )

    assert response.status_code == 204
    rounds = client.get(f"/jobs/{job_id}/interviews", headers=auth_headers).json()
    assert not any(r["id"] == round_["id"] for r in rounds)


def test_delete_interview_round_not_found(client, auth_headers, sample_job):
    # Deleting a non-existent round ID returns 404
    response = client.delete(
        f"/jobs/{sample_job['id']}/interviews/99999",
        headers=auth_headers,
    )

    assert response.status_code == 404
