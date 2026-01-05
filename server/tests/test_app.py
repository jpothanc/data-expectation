"""Tests for Flask application."""

import pytest


class TestApp:
    """Test cases for Flask application."""
    
    @pytest.mark.api
    def test_root_endpoint(self, client):
        """Test root endpoint."""
        response = client.get('/')
        
        assert response.status_code == 200
        data = response.get_json()
        assert 'message' in data
        assert 'version' in data
        assert 'endpoints' in data
    
    @pytest.mark.api
    def test_health_check(self, client):
        """Test health check endpoint."""
        response = client.get('/health')
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['status'] == 'healthy'
    
    @pytest.mark.api
    def test_api_docs_endpoint(self, client):
        """Test Swagger documentation endpoint."""
        response = client.get('/api-docs')
        
        # Should return Swagger UI or redirect
        assert response.status_code in [200, 302]
    
    @pytest.mark.api
    def test_apispec_endpoint(self, client):
        """Test Swagger JSON spec endpoint."""
        response = client.get('/apispec.json')
        
        assert response.status_code == 200
        data = response.get_json()
        assert 'swagger' in data or 'openapi' in data


