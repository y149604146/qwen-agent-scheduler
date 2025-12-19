"""Tests for Agent Scheduler Brain REST API

This module contains unit tests for the FastAPI REST endpoints.
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, MagicMock
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.api import AgentSchedulerAPI, TaskStatus
from shared.models import MethodMetadata, MethodParameter


@pytest.fixture
def api_instance():
    """Create API instance for testing"""
    return AgentSchedulerAPI()


@pytest.fixture
def client(api_instance):
    """Create test client"""
    return TestClient(api_instance.app)


@pytest.fixture
def mock_agent_client():
    """Create mock agent client"""
    mock = Mock()
    mock_response = Mock()
    mock_response.success = True
    mock_response.response = "Task completed successfully"
    mock_response.error = None
    mock.process_task.return_value = mock_response
    return mock


@pytest.fixture
def mock_method_loader():
    """Create mock method loader"""
    mock = Mock()
    
    # Create sample method metadata
    param1 = MethodParameter(
        name="city",
        type="string",
        description="City name",
        required=True
    )
    
    method1 = MethodMetadata(
        id=1,
        name="get_weather",
        description="Get weather information",
        parameters_json='[{"name": "city", "type": "string", "description": "City name", "required": true, "default": null}]',
        return_type="dict",
        module_path="tools.weather",
        function_name="get_weather"
    )
    
    mock.load_all_methods.return_value = [method1]
    return mock


class TestHealthEndpoints:
    """Tests for health check endpoints"""
    
    def test_root_endpoint(self, client):
        """Test root endpoint returns OK status"""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert "service" in data
    
    def test_health_check_endpoint(self, client):
        """Test health check endpoint"""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert data["status"] == "healthy"


class TestTaskSubmission:
    """Tests for task submission endpoint"""
    
    def test_submit_task_success(self, client, api_instance, mock_agent_client):
        """Test successful task submission"""
        api_instance.set_agent_client(mock_agent_client)
        
        response = client.post(
            "/api/tasks",
            json={"task_description": "Get weather for Seattle"}
        )
        
        assert response.status_code == 201
        data = response.json()
        assert "task_id" in data
        assert "status" in data
        assert data["status"] in [TaskStatus.PENDING, TaskStatus.PROCESSING, TaskStatus.COMPLETED]
    
    def test_submit_task_empty_description(self, client):
        """Test task submission with empty description returns 422 (Pydantic validation)"""
        response = client.post(
            "/api/tasks",
            json={"task_description": ""}
        )
        
        # Pydantic validation returns 422 for empty strings that have min_length constraint
        assert response.status_code == 422
        data = response.json()
        assert "detail" in data
    
    def test_submit_task_whitespace_description(self, client):
        """Test task submission with whitespace-only description returns 400"""
        response = client.post(
            "/api/tasks",
            json={"task_description": "   "}
        )
        
        assert response.status_code == 400
    
    def test_submit_task_invalid_json(self, client):
        """Test task submission with invalid JSON returns 422"""
        response = client.post(
            "/api/tasks",
            data="invalid json",
            headers={"Content-Type": "application/json"}
        )
        
        assert response.status_code == 422


class TestTaskStatusQuery:
    """Tests for task status query endpoint"""
    
    def test_query_existing_task(self, client, api_instance, mock_agent_client):
        """Test querying status of existing task"""
        api_instance.set_agent_client(mock_agent_client)
        
        # Submit a task first
        submit_response = client.post(
            "/api/tasks",
            json={"task_description": "Test task"}
        )
        task_id = submit_response.json()["task_id"]
        
        # Query the task status
        response = client.get(f"/api/tasks/{task_id}")
        
        assert response.status_code == 200
        data = response.json()
        assert data["task_id"] == task_id
        assert "status" in data
        assert "created_at" in data
    
    def test_query_nonexistent_task(self, client):
        """Test querying non-existent task returns 404"""
        response = client.get("/api/tasks/nonexistent-task-id")
        
        assert response.status_code == 404
        data = response.json()
        assert "detail" in data
    
    def test_completed_task_has_result(self, client, api_instance, mock_agent_client):
        """Test completed task includes result"""
        api_instance.set_agent_client(mock_agent_client)
        
        # Submit and complete a task
        submit_response = client.post(
            "/api/tasks",
            json={"task_description": "Test task"}
        )
        task_id = submit_response.json()["task_id"]
        
        # Query the task
        response = client.get(f"/api/tasks/{task_id}")
        data = response.json()
        
        if data["status"] == TaskStatus.COMPLETED:
            assert "result" in data
            assert data["completed_at"] is not None


class TestMethodsListing:
    """Tests for methods listing endpoint"""
    
    def test_list_methods_success(self, client, api_instance, mock_method_loader):
        """Test successful methods listing"""
        api_instance.set_method_loader(mock_method_loader)
        
        response = client.get("/api/methods")
        
        assert response.status_code == 200
        data = response.json()
        assert "methods" in data
        assert "count" in data
        assert data["count"] == len(data["methods"])
    
    def test_list_methods_without_loader(self, client):
        """Test methods listing without method loader returns 500"""
        response = client.get("/api/methods")
        
        assert response.status_code == 500
        data = response.json()
        assert "detail" in data
    
    def test_method_info_structure(self, client, api_instance, mock_method_loader):
        """Test that method info has correct structure"""
        api_instance.set_method_loader(mock_method_loader)
        
        response = client.get("/api/methods")
        data = response.json()
        
        if data["count"] > 0:
            method = data["methods"][0]
            assert "name" in method
            assert "description" in method
            assert "parameters" in method
            assert "return_type" in method


class TestErrorHandling:
    """Tests for error handling"""
    
    def test_server_error_response_format(self, client, api_instance):
        """Test that server errors return proper format"""
        # Mock method loader to raise exception
        mock_loader = Mock()
        mock_loader.load_all_methods.side_effect = Exception("Database error")
        api_instance.set_method_loader(mock_loader)
        
        response = client.get("/api/methods")
        
        assert response.status_code == 500
        data = response.json()
        assert "detail" in data


class TestTaskProcessing:
    """Tests for task processing flow"""
    
    def test_task_processing_with_agent_failure(self, client, api_instance):
        """Test task processing when agent fails"""
        # Mock agent that returns failure
        mock_agent = Mock()
        mock_response = Mock()
        mock_response.success = False
        mock_response.error = "Agent processing failed"
        mock_agent.process_task.return_value = mock_response
        
        api_instance.set_agent_client(mock_agent)
        
        # Submit task
        response = client.post(
            "/api/tasks",
            json={"task_description": "Test task"}
        )
        task_id = response.json()["task_id"]
        
        # Check task status
        status_response = client.get(f"/api/tasks/{task_id}")
        data = status_response.json()
        
        assert data["status"] == TaskStatus.FAILED
        assert data["error"] is not None
