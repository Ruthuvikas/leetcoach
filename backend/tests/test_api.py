import pytest
from fastapi.testclient import TestClient
from main import app
from models import Base
from database import engine

# Create test database
Base.metadata.create_all(bind=engine)

client = TestClient(app)


class TestQuestionsAPI:
    """Test questions endpoints"""
    
    def test_get_questions(self):
        """Test getting all questions"""
        response = client.get("/api/questions")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) > 0
        assert "id" in data[0]
        assert "title" in data[0]
    
    def test_start_session_valid(self):
        """Test starting a session with valid question ID"""
        response = client.post("/api/start-session", json={"question_id": 1})
        assert response.status_code == 200
        data = response.json()
        assert "question" in data
        assert data["question"]["id"] == 1
    
    def test_start_session_invalid_id(self):
        """Test starting a session with invalid question ID"""
        response = client.post("/api/start-session", json={"question_id": 999})
        assert response.status_code == 200  # Should return first question as default
        data = response.json()
        assert "question" in data


class TestFunctionDefinitionAPI:
    """Test function definition endpoint"""
    
    def test_function_definition_valid(self):
        """Test getting function definition with valid parameters"""
        response = client.post("/api/function-definition", json={
            "question_id": 1,
            "language": "python"
        })
        assert response.status_code == 200
        data = response.json()
        assert "function_definition" in data
        assert len(data["function_definition"]) > 0
    
    def test_function_definition_invalid_language(self):
        """Test getting function definition with invalid language"""
        response = client.post("/api/function-definition", json={
            "question_id": 1,
            "language": "invalid_lang"
        })
        assert response.status_code == 422  # Validation error
    
    def test_function_definition_missing_params(self):
        """Test getting function definition with missing parameters"""
        response = client.post("/api/function-definition", json={
            "question_id": 1
        })
        assert response.status_code == 422  # Validation error


class TestClarifyAPI:
    """Test clarify endpoint"""
    
    def test_clarify_valid_input(self):
        """Test clarify with valid input"""
        response = client.post("/api/clarify", json={
            "user_input": "What should I return if there's no solution?",
            "question_id": 1
        })
        assert response.status_code == 200
        data = response.json()
        assert "agent" in data
        assert "response" in data
    
    def test_clarify_empty_input(self):
        """Test clarify with empty input"""
        response = client.post("/api/clarify", json={
            "user_input": "",
            "question_id": 1
        })
        assert response.status_code == 422  # Validation error
    
    def test_clarify_long_input(self):
        """Test clarify with input that's too long"""
        long_input = "a" * 1001  # Over 1000 character limit
        response = client.post("/api/clarify", json={
            "user_input": long_input,
            "question_id": 1
        })
        assert response.status_code == 422  # Validation error


class TestBruteForceAPI:
    """Test brute force endpoint"""
    
    def test_brute_force_valid_input(self):
        """Test brute force with valid input"""
        response = client.post("/api/brute-force", json={
            "user_idea": "I'll use nested loops to check every pair",
            "time_complexity": "O(n^2)",
            "space_complexity": "O(1)",
            "question_id": 1
        })
        assert response.status_code == 200
        data = response.json()
        assert "agent" in data
        assert "response" in data
    
    def test_brute_force_empty_idea(self):
        """Test brute force with empty idea"""
        response = client.post("/api/brute-force", json={
            "user_idea": "",
            "question_id": 1
        })
        assert response.status_code == 422  # Validation error


class TestOptimizeAPI:
    """Test optimize endpoint"""
    
    def test_optimize_valid_input(self):
        """Test optimize with valid input"""
        response = client.post("/api/optimize", json={
            "user_idea": "I can use a hash map to improve efficiency",
            "time_complexity": "O(n)",
            "space_complexity": "O(n)",
            "question_id": 1
        })
        assert response.status_code == 200
        data = response.json()
        assert "agent" in data
        assert "response" in data


class TestCodeReviewAPI:
    """Test code review endpoint"""
    
    def test_code_review_valid_input(self):
        """Test code review with valid input"""
        response = client.post("/api/code-review", json={
            "clarification": "I need to find two numbers that sum to target",
            "brute_force": "Use nested loops to check all pairs",
            "code": "def twoSum(nums, target):\n    pass",
            "language": "python",
            "question_id": 1
        })
        assert response.status_code == 200
        data = response.json()
        assert "agent" in data
        assert "review" in data
    
    def test_code_review_empty_code(self):
        """Test code review with empty code"""
        response = client.post("/api/code-review", json={
            "clarification": "Test",
            "brute_force": "Test",
            "code": "",
            "language": "python",
            "question_id": 1
        })
        assert response.status_code == 422  # Validation error


class TestHealthCheck:
    """Test health check endpoint"""
    
    def test_health_check(self):
        """Test health check endpoint"""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "timestamp" in data


if __name__ == "__main__":
    pytest.main([__file__]) 