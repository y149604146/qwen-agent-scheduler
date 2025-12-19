"""REST API for Agent Scheduler Brain

This module provides RESTful API endpoints for task submission,
status queries, and method listing using FastAPI.
"""

import logging
import uuid
from datetime import datetime
from typing import Dict, Any, Optional, List
from enum import Enum

from fastapi import FastAPI, HTTPException, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from shared.models import MethodMetadata


logger = logging.getLogger(__name__)


class TaskStatus(str, Enum):
    """Task execution status"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class TaskSubmissionRequest(BaseModel):
    """Request model for task submission"""
    task_description: str = Field(..., min_length=1, description="Natural language task description")


class TaskSubmissionResponse(BaseModel):
    """Response model for task submission"""
    task_id: str = Field(..., description="Unique task identifier")
    status: TaskStatus = Field(..., description="Current task status")
    result: Optional[Any] = Field(None, description="Task result if completed")
    error: Optional[str] = Field(None, description="Error message if failed")


class TaskStatusResponse(BaseModel):
    """Response model for task status query"""
    task_id: str = Field(..., description="Unique task identifier")
    status: TaskStatus = Field(..., description="Current task status")
    result: Optional[Any] = Field(None, description="Task result if completed")
    error: Optional[str] = Field(None, description="Error message if failed")
    created_at: str = Field(..., description="Task creation timestamp")
    completed_at: Optional[str] = Field(None, description="Task completion timestamp")


class MethodInfo(BaseModel):
    """Information about a registered method"""
    name: str = Field(..., description="Method name")
    description: str = Field(..., description="Method description")
    parameters: List[Dict[str, Any]] = Field(..., description="Parameter definitions")
    return_type: str = Field(..., description="Return value type")


class MethodsListResponse(BaseModel):
    """Response model for methods list"""
    methods: List[MethodInfo] = Field(..., description="List of registered methods")
    count: int = Field(..., description="Total number of methods")


class ErrorResponse(BaseModel):
    """Error response model"""
    error: str = Field(..., description="Error message")
    detail: Optional[str] = Field(None, description="Detailed error information")


class TaskStore:
    """In-memory storage for task information
    
    In a production system, this would be replaced with a database
    or distributed cache like Redis.
    """
    
    def __init__(self):
        self._tasks: Dict[str, Dict[str, Any]] = {}
    
    def create_task(self, task_description: str) -> str:
        """Create a new task and return its ID"""
        task_id = str(uuid.uuid4())
        self._tasks[task_id] = {
            'task_id': task_id,
            'description': task_description,
            'status': TaskStatus.PENDING,
            'result': None,
            'error': None,
            'created_at': datetime.utcnow().isoformat() + 'Z',
            'completed_at': None
        }
        logger.info(f"Created task {task_id}")
        return task_id
    
    def get_task(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve task information by ID"""
        return self._tasks.get(task_id)
    
    def update_task_status(self, task_id: str, status: TaskStatus) -> None:
        """Update task status"""
        if task_id in self._tasks:
            self._tasks[task_id]['status'] = status
            logger.debug(f"Task {task_id} status updated to {status}")
    
    def complete_task(self, task_id: str, result: Any) -> None:
        """Mark task as completed with result"""
        if task_id in self._tasks:
            self._tasks[task_id]['status'] = TaskStatus.COMPLETED
            self._tasks[task_id]['result'] = result
            self._tasks[task_id]['completed_at'] = datetime.utcnow().isoformat() + 'Z'
            logger.info(f"Task {task_id} completed successfully")
    
    def fail_task(self, task_id: str, error: str) -> None:
        """Mark task as failed with error message"""
        if task_id in self._tasks:
            self._tasks[task_id]['status'] = TaskStatus.FAILED
            self._tasks[task_id]['error'] = error
            self._tasks[task_id]['completed_at'] = datetime.utcnow().isoformat() + 'Z'
            logger.error(f"Task {task_id} failed: {error}")


class AgentSchedulerAPI:
    """FastAPI application for Agent Scheduler Brain
    
    Provides REST endpoints for:
    - Task submission (POST /api/tasks)
    - Task status query (GET /api/tasks/{task_id})
    - Methods listing (GET /api/methods)
    
    Attributes:
        app: FastAPI application instance
        task_store: In-memory task storage
        agent_client: qwen-agent client for task processing
        method_loader: Method loader for retrieving registered methods
    """
    
    def __init__(self):
        """Initialize the API application"""
        self.app = FastAPI(
            title="Agent Scheduler Brain API",
            description="REST API for qwen-agent task scheduling and method execution",
            version="1.0.0"
        )
        
        self.task_store = TaskStore()
        self.agent_client = None
        self.method_loader = None
        
        # Register routes
        self._register_routes()
        
        logger.info("AgentSchedulerAPI initialized")
    
    def set_agent_client(self, agent_client) -> None:
        """Set the agent client for task processing
        
        Args:
            agent_client: AgentClient instance
        """
        self.agent_client = agent_client
        logger.info("Agent client registered with API")
    
    def set_method_loader(self, method_loader) -> None:
        """Set the method loader for retrieving methods
        
        Args:
            method_loader: MethodLoader instance
        """
        self.method_loader = method_loader
        logger.info("Method loader registered with API")
    
    def _register_routes(self) -> None:
        """Register all API routes"""
        
        @self.app.get("/", tags=["Health"])
        async def root():
            """Root endpoint - health check"""
            return {"status": "ok", "service": "Agent Scheduler Brain"}
        
        @self.app.get("/health", tags=["Health"])
        async def health_check():
            """Health check endpoint"""
            return {
                "status": "healthy",
                "agent_client": self.agent_client is not None,
                "method_loader": self.method_loader is not None
            }
        
        @self.app.post(
            "/api/tasks",
            response_model=TaskSubmissionResponse,
            status_code=status.HTTP_201_CREATED,
            tags=["Tasks"],
            responses={
                400: {"model": ErrorResponse, "description": "Invalid request"},
                500: {"model": ErrorResponse, "description": "Server error"}
            }
        )
        async def submit_task(request: TaskSubmissionRequest):
            """Submit a new task for processing
            
            Args:
                request: Task submission request with task description
                
            Returns:
                TaskSubmissionResponse with task_id and status
                
            Raises:
                HTTPException: If request is invalid or processing fails
            """
            try:
                # Validate request
                if not request.task_description or not request.task_description.strip():
                    logger.warning("Task submission rejected: empty task description")
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Task description cannot be empty"
                    )
                
                # Create task
                task_id = self.task_store.create_task(request.task_description)
                
                # Process task asynchronously (in a real system, use background tasks)
                # For now, we'll process synchronously
                if self.agent_client is not None:
                    try:
                        self.task_store.update_task_status(task_id, TaskStatus.PROCESSING)
                        
                        # Process the task
                        response = self.agent_client.process_task(request.task_description)
                        
                        if response.success:
                            self.task_store.complete_task(task_id, response.response)
                        else:
                            self.task_store.fail_task(task_id, response.error or "Unknown error")
                    except Exception as e:
                        logger.error(f"Task processing failed: {e}")
                        self.task_store.fail_task(task_id, str(e))
                else:
                    logger.warning("Agent client not configured, task remains pending")
                
                task = self.task_store.get_task(task_id)
                return TaskSubmissionResponse(
                    task_id=task_id,
                    status=task['status'],
                    result=task['result'],
                    error=task['error']
                )
                
            except HTTPException:
                raise
            except Exception as e:
                logger.error(f"Task submission failed: {e}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Failed to submit task: {str(e)}"
                )
        
        @self.app.get(
            "/api/tasks/{task_id}",
            response_model=TaskStatusResponse,
            tags=["Tasks"],
            responses={
                404: {"model": ErrorResponse, "description": "Task not found"},
                500: {"model": ErrorResponse, "description": "Server error"}
            }
        )
        async def get_task_status(task_id: str):
            """Query task status and result
            
            Args:
                task_id: Unique task identifier
                
            Returns:
                TaskStatusResponse with task status and result
                
            Raises:
                HTTPException: If task not found or query fails
            """
            try:
                task = self.task_store.get_task(task_id)
                
                if task is None:
                    logger.warning(f"Task not found: {task_id}")
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail=f"Task '{task_id}' not found"
                    )
                
                return TaskStatusResponse(
                    task_id=task['task_id'],
                    status=task['status'],
                    result=task['result'],
                    error=task['error'],
                    created_at=task['created_at'],
                    completed_at=task['completed_at']
                )
                
            except HTTPException:
                raise
            except Exception as e:
                logger.error(f"Failed to query task status: {e}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Failed to query task status: {str(e)}"
                )
        
        @self.app.get(
            "/api/methods",
            response_model=MethodsListResponse,
            tags=["Methods"],
            responses={
                500: {"model": ErrorResponse, "description": "Server error"}
            }
        )
        async def list_methods():
            """List all registered methods
            
            Returns:
                MethodsListResponse with list of registered methods
                
            Raises:
                HTTPException: If query fails
            """
            try:
                if self.method_loader is None:
                    logger.error("Method loader not configured")
                    raise HTTPException(
                        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                        detail="Method loader not configured"
                    )
                
                # Load all methods
                methods = self.method_loader.load_all_methods()
                
                # Convert to response format
                method_infos = []
                for method in methods:
                    method_info = MethodInfo(
                        name=method.name,
                        description=method.description,
                        parameters=[p.to_dict() for p in method.parameters],
                        return_type=method.return_type
                    )
                    method_infos.append(method_info)
                
                logger.info(f"Returning {len(method_infos)} registered methods")
                
                return MethodsListResponse(
                    methods=method_infos,
                    count=len(method_infos)
                )
                
            except HTTPException:
                raise
            except Exception as e:
                logger.error(f"Failed to list methods: {e}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Failed to list methods: {str(e)}"
                )
        
        @self.app.exception_handler(Exception)
        async def global_exception_handler(request, exc):
            """Global exception handler for unhandled errors"""
            logger.error(f"Unhandled exception: {exc}", exc_info=True)
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={"error": "Internal server error", "detail": str(exc)}
            )


def create_app() -> FastAPI:
    """Factory function to create FastAPI application
    
    Returns:
        FastAPI application instance
    """
    api = AgentSchedulerAPI()
    return api.app
