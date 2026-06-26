"""Tests for AWS Secrets Manager client."""

import json
from unittest.mock import Mock, patch

import pytest
from botocore.exceptions import ClientError

from app.services.secrets.manager import (
    load_credentials,
    SecretNotFoundError,
    SecretAccessDeniedError,
)
from app.services.platform.browser import Credentials


@pytest.fixture
def mock_boto3_client():
    """Mock boto3 Secrets Manager client."""
    with patch('app.services.secrets.manager.boto3.session.Session') as mock_session:
        mock_client = Mock()
        mock_session.return_value.client.return_value = mock_client
        yield mock_client


def test_load_credentials_success(mock_boto3_client):
    """정상적으로 자격증명을 로드하는 경우."""
    # Arrange
    credential_key = "parapara/platform/user123/bunjang"
    secret_data = {"username": "testuser", "password": "testpass123"}
    
    mock_boto3_client.get_secret_value.return_value = {
        'SecretString': json.dumps(secret_data)
    }
    
    # Act
    result = load_credentials(credential_key)
    
    # Assert
    assert isinstance(result, Credentials)
    assert result.username == "testuser"
    assert result.password == "testpass123"
    mock_boto3_client.get_secret_value.assert_called_once_with(SecretId=credential_key)


def test_load_credentials_secret_not_found(mock_boto3_client):
    """시크릿이 존재하지 않는 경우."""
    # Arrange
    credential_key = "parapara/platform/user123/nonexistent"
    
    error_response = {
        'Error': {
            'Code': 'ResourceNotFoundException',
            'Message': 'Secret not found'
        }
    }
    mock_boto3_client.get_secret_value.side_effect = ClientError(
        error_response, 'GetSecretValue'
    )
    
    # Act & Assert
    with pytest.raises(SecretNotFoundError) as exc_info:
        load_credentials(credential_key)
    
    assert credential_key in str(exc_info.value)


def test_load_credentials_access_denied(mock_boto3_client):
    """시크릿 접근 권한이 없는 경우."""
    # Arrange
    credential_key = "parapara/platform/user123/bunjang"
    
    error_response = {
        'Error': {
            'Code': 'AccessDeniedException',
            'Message': 'Access denied'
        }
    }
    mock_boto3_client.get_secret_value.side_effect = ClientError(
        error_response, 'GetSecretValue'
    )
    
    # Act & Assert
    with pytest.raises(SecretAccessDeniedError) as exc_info:
        load_credentials(credential_key)
    
    assert credential_key in str(exc_info.value)


def test_load_credentials_invalid_json(mock_boto3_client):
    """시크릿이 유효한 JSON이 아닌 경우."""
    # Arrange
    credential_key = "parapara/platform/user123/bunjang"
    
    mock_boto3_client.get_secret_value.return_value = {
        'SecretString': 'not a valid json'
    }
    
    # Act & Assert
    with pytest.raises(ValueError) as exc_info:
        load_credentials(credential_key)
    
    assert "Invalid secret format" in str(exc_info.value)


def test_load_credentials_missing_username(mock_boto3_client):
    """username 필드가 누락된 경우."""
    # Arrange
    credential_key = "parapara/platform/user123/bunjang"
    secret_data = {"password": "testpass123"}  # username 누락
    
    mock_boto3_client.get_secret_value.return_value = {
        'SecretString': json.dumps(secret_data)
    }
    
    # Act & Assert
    with pytest.raises(ValueError) as exc_info:
        load_credentials(credential_key)
    
    assert "Missing required field" in str(exc_info.value)


def test_load_credentials_missing_password(mock_boto3_client):
    """password 필드가 누락된 경우."""
    # Arrange
    credential_key = "parapara/platform/user123/bunjang"
    secret_data = {"username": "testuser"}  # password 누락
    
    mock_boto3_client.get_secret_value.return_value = {
        'SecretString': json.dumps(secret_data)
    }
    
    # Act & Assert
    with pytest.raises(ValueError) as exc_info:
        load_credentials(credential_key)
    
    assert "Missing required field" in str(exc_info.value)


def test_load_credentials_no_credential_value_in_logs(mock_boto3_client, caplog):
    """로그에 자격증명 값(username/password)이 노출되지 않는지 확인."""
    # Arrange
    credential_key = "parapara/platform/user123/bunjang"
    secret_data = {"username": "testuser", "password": "super_secret_password_123"}
    
    mock_boto3_client.get_secret_value.return_value = {
        'SecretString': json.dumps(secret_data)
    }
    
    # Act
    with caplog.at_level('INFO'):
        result = load_credentials(credential_key)
    
    # Assert - credential_key는 로그에 있어야 함
    assert credential_key in caplog.text
    
    # Assert - 실제 username/password 값은 로그에 없어야 함
    assert "testuser" not in caplog.text
    assert "super_secret_password_123" not in caplog.text
    
    # 결과는 정상적으로 반환되어야 함
    assert result.username == "testuser"
    assert result.password == "super_secret_password_123"


def test_load_credentials_error_does_not_expose_values(mock_boto3_client, caplog):
    """오류 발생 시에도 자격증명 값이 로그에 노출되지 않는지 확인."""
    # Arrange
    credential_key = "parapara/platform/user123/bunjang"
    
    error_response = {
        'Error': {
            'Code': 'ResourceNotFoundException',
            'Message': 'Secret not found'
        }
    }
    mock_boto3_client.get_secret_value.side_effect = ClientError(
        error_response, 'GetSecretValue'
    )
    
    # Act & Assert
    with caplog.at_level('ERROR'):
        with pytest.raises(SecretNotFoundError):
            load_credentials(credential_key)
    
    # credential_key는 로그에 있어야 함
    assert credential_key in caplog.text
    
    # 오류 메시지에도 credential_key만 참조
    assert "key=" in caplog.text
