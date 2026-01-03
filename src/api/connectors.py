"""
Connector management API endpoints.
"""

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from datetime import datetime
from enum import Enum

router = APIRouter()


class AuthType(str, Enum):
    API_KEY = "api_key"
    OAUTH2 = "oauth2"
    BASIC = "basic"
    BEARER = "bearer"
    CUSTOM = "custom"


class ConnectorCreate(BaseModel):
    name: str
    description: str
    base_url: str
    auth_type: AuthType
    auth_config: Dict[str, Any]
    default_headers: Dict[str, str] = {}
    rate_limit: Optional[int] = None
    timeout: int = 30


class ConnectorResponse(BaseModel):
    id: str
    name: str
    description: str
    base_url: str
    auth_type: AuthType
    status: str
    created_at: datetime


class EndpointCreate(BaseModel):
    name: str
    method: str  # GET, POST, PUT, DELETE, PATCH
    path: str
    request_schema: Optional[Dict] = None
    response_schema: Optional[Dict] = None
    rate_limit: Optional[int] = None


@router.get("/", response_model=List[ConnectorResponse])
async def list_connectors():
    """List all configured connectors."""
    return []


@router.post("/", response_model=ConnectorResponse, status_code=status.HTTP_201_CREATED)
async def create_connector(connector: ConnectorCreate):
    """
    Create a new API connector.
    
    Connectors define connection to external APIs including:
    - Base URL
    - Authentication method
    - Default headers
    - Rate limiting
    """
    return {
        "id": "conn_abc123",
        "name": connector.name,
        "description": connector.description,
        "base_url": connector.base_url,
        "auth_type": connector.auth_type,
        "status": "active",
        "created_at": datetime.utcnow(),
    }


@router.get("/{connector_id}", response_model=ConnectorResponse)
async def get_connector(connector_id: str):
    """Get connector by ID."""
    raise HTTPException(status_code=404, detail="Connector not found")


@router.post("/{connector_id}/test")
async def test_connector(connector_id: str):
    """Test connector connectivity."""
    return {
        "connector_id": connector_id,
        "status": "success",
        "latency_ms": 150,
        "tested_at": datetime.utcnow().isoformat(),
    }


@router.post("/{connector_id}/endpoints", status_code=status.HTTP_201_CREATED)
async def add_endpoint(connector_id: str, endpoint: EndpointCreate):
    """Add an endpoint to a connector."""
    return {
        "id": "ep_xyz789",
        "connector_id": connector_id,
        "name": endpoint.name,
        "method": endpoint.method,
        "path": endpoint.path,
    }


@router.get("/{connector_id}/endpoints")
async def list_endpoints(connector_id: str):
    """List all endpoints for a connector."""
    return []
