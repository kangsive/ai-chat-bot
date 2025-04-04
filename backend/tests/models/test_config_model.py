import uuid
import pytest

from app.models.user import User
from app.models.config import UserConfig, SystemConfig


class TestUserConfigModel:
    def test_user_config_creation(self, db_session):
        """Test user config creation and association with user."""
        # Create a user first
        user = User(
            email="test@example.com",
            username="testuser",
            hashed_password="hashedpassword123"
        )
        db_session.add(user)
        db_session.commit()
        
        # Create user config
        config = UserConfig(
            user_id=user.id,
            preferences={
                "theme": "dark",
                "notifications": True,
                "default_model": "gpt-4"
            }
        )
        db_session.add(config)
        db_session.commit()
        
        # Query the config back
        db_config = db_session.query(UserConfig).filter(
            UserConfig.user_id == user.id
        ).first()
        
        assert db_config is not None
        assert db_config.user_id == user.id
        assert db_config.preferences["theme"] == "dark"
        assert db_config.preferences["notifications"] is True
        assert db_config.preferences["default_model"] == "gpt-4"
        
        # Check relationship
        assert db_config.user.username == "testuser"
        
        # Ensure timestamps are created
        assert db_config.created_at is not None
        assert db_config.updated_at is not None
    
    def test_user_config_update(self, db_session):
        """Test updating user config."""
        # Create a user first
        user = User(
            email="test@example.com",
            username="testuser",
            hashed_password="hashedpassword123"
        )
        db_session.add(user)
        db_session.commit()
        
        # Create user config
        config = UserConfig(
            user_id=user.id,
            preferences={
                "theme": "light",
                "notifications": False
            }
        )
        db_session.add(config)
        db_session.commit()
        
        # Update the config - create a new dictionary
        db_config = db_session.query(UserConfig).filter(
            UserConfig.user_id == user.id
        ).first()
        
        # Update preferences by creating a new dictionary with all values
        db_config.preferences = {
            **db_config.preferences,
            "theme": "dark",
            "font_size": "large"
        }
        db_session.commit()

        # The following is not allowed, it will raise an error
        """ When you directly modify a JSON/JSONB field using dictionary-style access like db_config.preferences["theme"] = "dark", SQLAlchemy doesn't always detect the change to trigger an update to the database.
            I've fixed it by:
            Replacing the dictionary update method with a complete reassignment of the preferences field
            Using dictionary unpacking (**db_config.preferences) to keep the existing values
            Adding the updated values to create a completely new dictionary
            This approach ensures that SQLAlchemy recognizes the change to the entire JSONB object and properly updates it in the database. The test should now pass because the updated values will be correctly stored and retrieved from the database."""
        # db_config.preferences["theme"] = "dark"
        # db_config.preferences["font_size"] = "large"
        
        # Query the updated config
        updated_config = db_session.query(UserConfig).filter(
            UserConfig.user_id == user.id
        ).first()
        
        assert updated_config.preferences["theme"] == "dark"
        assert updated_config.preferences["notifications"] is False
        assert updated_config.preferences["font_size"] == "large"


class TestSystemConfigModel:
    def test_system_config_creation(self, db_session):
        """Test system config creation."""
        # Create system configs
        config1 = SystemConfig(
            key="default_model",
            value="gpt-3.5-turbo",
            description="Default model to use for new chats"
        )
        
        config2 = SystemConfig(
            key="max_tokens",
            value=4096,
            description="Maximum tokens per request"
        )
        
        config3 = SystemConfig(
            key="available_models",
            value=["gpt-3.5-turbo", "gpt-4", "claude-3-opus"],
            description="Available models for selection"
        )
        
        db_session.add_all([config1, config2, config3])
        db_session.commit()
        
        # Query the configs back
        default_model = db_session.query(SystemConfig).filter(
            SystemConfig.key == "default_model"
        ).first()
        
        max_tokens = db_session.query(SystemConfig).filter(
            SystemConfig.key == "max_tokens"
        ).first()
        
        available_models = db_session.query(SystemConfig).filter(
            SystemConfig.key == "available_models"
        ).first()
        
        # Check default_model
        assert default_model is not None
        assert default_model.key == "default_model"
        assert default_model.value == "gpt-3.5-turbo"
        assert default_model.description == "Default model to use for new chats"
        
        # Check max_tokens
        assert max_tokens is not None
        assert max_tokens.key == "max_tokens"
        assert max_tokens.value == 4096
        assert max_tokens.description == "Maximum tokens per request"
        
        # Check available_models (array)
        assert available_models is not None
        assert available_models.key == "available_models"
        assert isinstance(available_models.value, list)
        assert len(available_models.value) == 3
        assert "gpt-4" in available_models.value
        
        # Ensure timestamps are created
        assert default_model.created_at is not None
        assert default_model.updated_at is not None
    
    def test_system_config_unique_key(self, db_session):
        """Test that system config keys must be unique."""
        # Create first config
        config1 = SystemConfig(
            key="api_timeout",
            value=30,
            description="API timeout in seconds"
        )
        db_session.add(config1)
        db_session.commit()
        
        # Create second config with the same key
        config2 = SystemConfig(
            key="api_timeout",
            value=60,
            description="Different description"
        )
        db_session.add(config2)
        
        # Should raise an integrity error
        with pytest.raises(Exception):
            db_session.commit()
        
        db_session.rollback()
    
    def test_system_config_complex_json(self, db_session):
        """Test system config with complex JSON structure."""
        # Create a config with complex nested JSON
        config = SystemConfig(
            key="rate_limits",
            value={
                "free_tier": {
                    "requests_per_day": 50,
                    "tokens_per_request": 2000
                },
                "premium_tier": {
                    "requests_per_day": 200,
                    "tokens_per_request": 4000
                },
                "enterprise": {
                    "requests_per_day": -1,  # unlimited
                    "tokens_per_request": 8000
                }
            },
            description="Rate limits for different user tiers"
        )
        db_session.add(config)
        db_session.commit()
        
        # Query the config back
        db_config = db_session.query(SystemConfig).filter(
            SystemConfig.key == "rate_limits"
        ).first()
        
        assert db_config is not None
        assert db_config.value["free_tier"]["requests_per_day"] == 50
        assert db_config.value["premium_tier"]["tokens_per_request"] == 4000
        assert db_config.value["enterprise"]["requests_per_day"] == -1 