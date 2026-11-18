"""Integration tests for the task API endpoints."""
from __future__ import annotations

from fastapi.testclient import TestClient

from app.main import app


def test_create_task():
    """POST /api/v1/tasks should create a new task."""
    client = TestClient(app)
    response = client.post(
        "/api/v1/tasks",
        json={"name": "API Test Task", "description": "Created via API", "input_payload": {"key": "value"}},
    )

    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "API Test Task"
    assert data["description"] == "Created via API"
    assert data["status"] == "PENDING"
    assert data["input_payload"] == {"key": "value"}
    assert "id" in data
    assert "created_at" in data


def test_create_task_minimal():
    """POST /api/v1/tasks should work with only required fields."""
    client = TestClient(app)
    response = client.post("/api/v1/tasks", json={"name": "Minimal Task"})

    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Minimal Task"
    assert data["status"] == "PENDING"


def test_create_task_validation():
    """POST /api/v1/tasks should reject invalid input."""
    client = TestClient(app)
    response = client.post("/api/v1/tasks", json={"name": ""})
    assert response.status_code == 422


def test_list_tasks():
    """GET /api/v1/tasks should list tasks with pagination."""
    client = TestClient(app)

    # Create a few tasks
    for i in range(3):
        client.post("/api/v1/tasks", json={"name": f"Task {i}"})

    response = client.get("/api/v1/tasks?page=1&page_size=2")

    assert response.status_code == 200
    data = response.json()
    assert len(data["items"]) == 2
    assert data["page"] == 1
    assert data["page_size"] == 2
    assert data["total"] >= 3
    assert data["has_next"] is True


def test_list_tasks_filter_by_status():
    """GET /api/v1/tasks should filter by status."""
    client = TestClient(app)
    client.post("/api/v1/tasks", json={"name": "Pending Task"})
    client.post("/api/v1/tasks", json={"name": "Another Pending Task"})

    response = client.get("/api/v1/tasks?status=PENDING")

    assert response.status_code == 200
    data = response.json()
    for item in data["items"]:
        assert item["status"] == "PENDING"


def test_get_task():
    """GET /api/v1/tasks/{id} should retrieve a single task."""
    client = TestClient(app)
    create_resp = client.post("/api/v1/tasks", json={"name": "Get Task"})
    task_id = create_resp.json()["id"]

    response = client.get(f"/api/v1/tasks/{task_id}")

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == task_id
    assert data["name"] == "Get Task"


def test_get_task_not_found():
    """GET /api/v1/tasks/{id} should return 404 for non-existent task."""
    client = TestClient(app)
    fake_id = "00000000-0000-0000-0000-000000000000"
    response = client.get(f"/api/v1/tasks/{fake_id}")

    assert response.status_code == 404


def test_get_task_invalid_uuid():
    """GET /api/v1/tasks/{id} should return 400 for invalid UUID."""
    client = TestClient(app)
    response = client.get("/api/v1/tasks/not-a-uuid")

    assert response.status_code == 400


def test_execute_task():
    """POST /api/v1/tasks/{id}/execute should execute a pending task."""
    client = TestClient(app)
    create_resp = client.post(
        "/api/v1/tasks",
        json={"name": "Execute Task", "input_payload": {"data": "test"}},
    )
    task_id = create_resp.json()["id"]

    response = client.post(f"/api/v1/tasks/{task_id}/execute")

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == task_id
    assert data["status"] == "COMPLETED"
    assert data["output_payload"] is not None


def test_execute_task_already_completed():
    """POST /api/v1/tasks/{id}/execute should fail for already executed task."""
    client = TestClient(app)
    create_resp = client.post("/api/v1/tasks", json={"name": "Execute Once"})
    task_id = create_resp.json()["id"]

    client.post(f"/api/v1/tasks/{task_id}/execute")
    response = client.post(f"/api/v1/tasks/{task_id}/execute")

    assert response.status_code == 400
    data = response.json()
    assert "cannot be executed" in data["detail"].lower()


def test_execute_task_not_found():
    """POST /api/v1/tasks/{id}/execute should return 404 for non-existent task."""
    client = TestClient(app)
    fake_id = "00000000-0000-0000-0000-000000000000"
    response = client.post(f"/api/v1/tasks/{fake_id}/execute")

    assert response.status_code == 404


def test_cancel_task():
    """POST /api/v1/tasks/{id}/cancel should cancel a pending task."""
    client = TestClient(app)
    create_resp = client.post("/api/v1/tasks", json={"name": "Cancel Task"})
    task_id = create_resp.json()["id"]

    response = client.post(f"/api/v1/tasks/{task_id}/cancel")

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "CANCELLED"


def test_cancel_task_not_pending():
    """POST /api/v1/tasks/{id}/cancel should fail for non-pending task."""
    client = TestClient(app)
    create_resp = client.post("/api/v1/tasks", json={"name": "Execute Then Cancel"})
    task_id = create_resp.json()["id"]

    client.post(f"/api/v1/tasks/{task_id}/execute")
    response = client.post(f"/api/v1/tasks/{task_id}/cancel")

    assert response.status_code == 400
    data = response.json()
    assert "cannot be cancelled" in data["detail"].lower()


def test_get_task_result():
    """GET /api/v1/tasks/{id}/result should return execution result."""
    client = TestClient(app)
    create_resp = client.post(
        "/api/v1/tasks", json={"name": "Result Task", "input_payload": {"x": 1}}
    )
    task_id = create_resp.json()["id"]

    client.post(f"/api/v1/tasks/{task_id}/execute")
    response = client.get(f"/api/v1/tasks/{task_id}/result")

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == task_id
    assert data["status"] == "COMPLETED"
    assert data["output_payload"] is not None


def test_get_task_result_pending():
    """GET /api/v1/tasks/{id}/result should work for pending task (returns no output)."""
    client = TestClient(app)
    create_resp = client.post("/api/v1/tasks", json={"name": "Pending Result"})
    task_id = create_resp.json()["id"]

    response = client.get(f"/api/v1/tasks/{task_id}/result")

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "PENDING"
    assert data["output_payload"] is None
    assert data["error_message"] is None


def test_full_task_lifecycle():
    """Test the complete task lifecycle: create -> execute -> get result."""
    client = TestClient(app)

    # Create
    create_resp = client.post(
        "/api/v1/tasks",
        json={"name": "Lifecycle Task", "input_payload": {"step": 1}},
    )
    assert create_resp.status_code == 201
    task_id = create_resp.json()["id"]

    # Execute
    exec_resp = client.post(f"/api/v1/tasks/{task_id}/execute")
    assert exec_resp.status_code == 200
    assert exec_resp.json()["status"] == "COMPLETED"

    # Get result
    result_resp = client.get(f"/api/v1/tasks/{task_id}/result")
    assert result_resp.status_code == 200
    assert result_resp.json()["output_payload"] is not None

    # Verify status in list
    list_resp = client.get("/api/v1/tasks")
    assert list_resp.status_code == 200
    items = list_resp.json()["items"]
    task = next((t for t in items if t["id"] == task_id), None)
    assert task is not None
    assert task["status"] == "COMPLETED"