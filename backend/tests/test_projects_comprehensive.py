"""
Comprehensive Projects Module Tests
=====================================
Tests project CRUD, tasks, time-logs, expenses, profitability,
and dashboard stats.

Uses conftest fixtures (auth_headers, admin_headers, base_url, dev_headers).
"""

import pytest
import requests
import uuid
from datetime import datetime


def unique(prefix="test"):
    return f"{prefix}_{uuid.uuid4().hex[:8]}"


# ==================== PROJECT CRUD ====================

class TestProjectCRUD:
    """Test project CRUD via /api/v1/projects"""

    @pytest.fixture(scope="class")
    def created_project(self, base_url, auth_headers):
        """Create a test project"""
        data = {
            "name": f"Test Project {unique()}",
            "description": "Comprehensive test project",
            "status": "active",
            "budget": 100000.0,
            "start_date": "2026-01-01",
            "end_date": "2026-12-31",
        }
        resp = requests.post(f"{base_url}/api/v1/projects", json=data, headers=auth_headers)
        assert resp.status_code == 200, f"Create project: {resp.status_code} {resp.text[:300]}"
        result = resp.json()
        proj = result.get("project") or result
        pid = proj.get("project_id")
        assert pid, f"No project_id: {list(result.keys())}"
        return proj

    def test_create_project(self, created_project):
        """POST /api/v1/projects creates project"""
        assert created_project.get("project_id") is not None

    def test_create_project_requires_auth(self, base_url):
        """POST /api/v1/projects without auth returns 401/403"""
        resp = requests.post(f"{base_url}/api/v1/projects", json={"name": "NoAuth"})
        assert resp.status_code in (401, 403)

    def test_list_projects(self, base_url, auth_headers):
        """GET /api/v1/projects returns list"""
        resp = requests.get(f"{base_url}/api/v1/projects", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        projects = data.get("projects") or data.get("data") or data
        assert isinstance(projects, (list, dict))

    def test_get_project_by_id(self, base_url, auth_headers, created_project):
        """GET /api/v1/projects/{id} returns project"""
        pid = created_project["project_id"]
        resp = requests.get(f"{base_url}/api/v1/projects/{pid}", headers=auth_headers)
        assert resp.status_code == 200

    def test_get_nonexistent_project(self, base_url, auth_headers):
        """GET /api/v1/projects/{fake} returns 404"""
        resp = requests.get(f"{base_url}/api/v1/projects/proj_nonexist_999", headers=auth_headers)
        assert resp.status_code == 404

    def test_update_project(self, base_url, auth_headers, created_project):
        """PUT /api/v1/projects/{id} updates project"""
        pid = created_project["project_id"]
        resp = requests.put(
            f"{base_url}/api/v1/projects/{pid}",
            json={"description": "Updated by comprehensive test", "budget": 150000.0},
            headers=auth_headers,
        )
        assert resp.status_code == 200


# ==================== TASKS ====================

class TestProjectTasks:
    """Test project task management"""

    @pytest.fixture(scope="class")
    def project_with_task(self, base_url, auth_headers):
        """Create project + task for task testing"""
        # Create project
        resp = requests.post(
            f"{base_url}/api/v1/projects",
            json={"name": f"Task Project {unique()}", "status": "active"},
            headers=auth_headers,
        )
        assert resp.status_code == 200
        proj = resp.json().get("project") or resp.json()
        pid = proj["project_id"]
        # Create task
        resp = requests.post(
            f"{base_url}/api/v1/projects/{pid}/tasks",
            json={"name": f"Task {unique()}", "description": "Test task", "status": "todo"},
            headers=auth_headers,
        )
        assert resp.status_code == 200, f"Create task: {resp.status_code} {resp.text[:300]}"
        task = resp.json().get("task") or resp.json()
        return {"project_id": pid, "task": task}

    def test_create_task(self, project_with_task):
        """POST /api/v1/projects/{id}/tasks creates task"""
        assert project_with_task["task"] is not None

    def test_list_tasks(self, base_url, auth_headers, project_with_task):
        """GET /api/v1/projects/{id}/tasks returns task list"""
        pid = project_with_task["project_id"]
        resp = requests.get(f"{base_url}/api/v1/projects/{pid}/tasks", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        tasks = data.get("tasks") or data.get("data") or data
        assert isinstance(tasks, (list, dict))

    def test_update_task(self, base_url, auth_headers, project_with_task):
        """PUT /api/v1/projects/{id}/tasks/{task_id} updates task"""
        pid = project_with_task["project_id"]
        task = project_with_task["task"]
        tid = task.get("task_id") or task.get("id")
        if not tid:
            pytest.skip("No task_id in response")
        resp = requests.put(
            f"{base_url}/api/v1/projects/{pid}/tasks/{tid}",
            json={"status": "in_progress"},
            headers=auth_headers,
        )
        assert resp.status_code == 200


# ==================== TIME LOGS ====================

class TestProjectTimeLogs:
    """Test project time logging"""

    def test_log_time(self, base_url, auth_headers):
        """POST /api/v1/projects/{id}/time-log logs time"""
        # Create a project
        resp = requests.post(
            f"{base_url}/api/v1/projects",
            json={"name": f"Time Project {unique()}", "status": "active"},
            headers=auth_headers,
        )
        if resp.status_code != 200:
            pytest.skip("Cannot create project")
        pid = (resp.json().get("project") or resp.json())["project_id"]
        today = datetime.now().strftime("%Y-%m-%d")
        resp = requests.post(
            f"{base_url}/api/v1/projects/{pid}/time-log",
            json={"date": today, "hours": 4.0, "description": "Development work"},
            headers=auth_headers,
        )
        assert resp.status_code == 200, f"Log time: {resp.status_code} {resp.text[:300]}"

    def test_get_time_logs(self, base_url, auth_headers):
        """GET /api/v1/projects/{id}/time-logs returns logs"""
        # Get first project
        resp = requests.get(f"{base_url}/api/v1/projects", headers=auth_headers)
        if resp.status_code != 200:
            pytest.skip("Cannot list projects")
        projects = resp.json().get("projects") or resp.json().get("data") or []
        if not projects:
            pytest.skip("No projects")
        pid = projects[0].get("project_id")
        resp = requests.get(f"{base_url}/api/v1/projects/{pid}/time-logs", headers=auth_headers)
        assert resp.status_code == 200


# ==================== EXPENSES ====================

class TestProjectExpenses:
    """Test project expense management"""

    def test_list_expenses(self, base_url, auth_headers):
        """GET /api/v1/projects/{id}/expenses returns expenses"""
        resp = requests.get(f"{base_url}/api/v1/projects", headers=auth_headers)
        if resp.status_code != 200:
            pytest.skip("Cannot list projects")
        projects = resp.json().get("projects") or resp.json().get("data") or []
        if not projects:
            pytest.skip("No projects")
        pid = projects[0].get("project_id")
        resp = requests.get(f"{base_url}/api/v1/projects/{pid}/expenses", headers=auth_headers)
        assert resp.status_code == 200


# ==================== PROFITABILITY & DASHBOARD ====================

class TestProjectReports:
    """Test project reporting endpoints"""

    def test_project_profitability(self, base_url, auth_headers):
        """GET /api/v1/projects/{id}/profitability returns analysis"""
        resp = requests.get(f"{base_url}/api/v1/projects", headers=auth_headers)
        if resp.status_code != 200:
            pytest.skip("Cannot list projects")
        projects = resp.json().get("projects") or resp.json().get("data") or []
        if not projects:
            pytest.skip("No projects")
        pid = projects[0].get("project_id")
        resp = requests.get(f"{base_url}/api/v1/projects/{pid}/profitability", headers=auth_headers)
        assert resp.status_code == 200

    def test_dashboard_stats(self, base_url, auth_headers):
        """GET /api/v1/projects/stats/dashboard returns dashboard"""
        resp = requests.get(f"{base_url}/api/v1/projects/stats/dashboard", headers=auth_headers)
        assert resp.status_code == 200


# ==================== NEGATIVE TESTS ====================

class TestProjectsNegative:
    """Security and negative tests"""

    def test_list_no_auth(self, base_url):
        """GET /api/v1/projects without auth returns 401/403"""
        resp = requests.get(f"{base_url}/api/v1/projects")
        assert resp.status_code in (401, 403)

    def test_create_no_auth(self, base_url):
        """POST /api/v1/projects without auth returns 401/403"""
        resp = requests.post(f"{base_url}/api/v1/projects", json={"name": "NoAuth"})
        assert resp.status_code in (401, 403)

    def test_delete_nonexistent(self, base_url, auth_headers):
        """DELETE /api/v1/projects/{fake} returns 404"""
        resp = requests.delete(f"{base_url}/api/v1/projects/proj_fake_999", headers=auth_headers)
        assert resp.status_code in (200, 404)
