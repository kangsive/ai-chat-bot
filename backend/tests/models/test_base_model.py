import pytest
from datetime import datetime, timedelta
from time import sleep

from sqlalchemy import Column, String, Integer
from sqlalchemy.ext.declarative import declarative_base

from app.models.base import Base


class TestBaseModel:
    def test_tablename_generation(self, db_session):
        """Test that tablename is automatically generated from class name."""
        print("\n=== Starting test_tablename_generation ===")
        
        # Define a model class inheriting from Base
        class TestModel(Base):
            id = Column(Integer, primary_key=True)
            name = Column(String(50))
            value = Column(Integer)
        
        print("Model class defined")
        
        # Create the tables
        Base.metadata.create_all(bind=db_session.bind, tables=[TestModel.__table__])
        print(f"Tables created: {TestModel.__tablename__}")
        
        # Check tablename
        assert TestModel.__tablename__ == "testmodel"
        print("Verified tablename is correct")
        
        # Clean up - use safer approach to clean up
        print("Starting cleanup...")
        try:
            # Close the current session explicitly
            db_session.close()
            print("Session closed")
            
            # Drop using SQL execute instead of direct table drop
            db_session.execute(f"DROP TABLE IF EXISTS {TestModel.__tablename__}")
            db_session.commit()
            print("Table dropped via SQL command")
        except Exception as e:
            print(f"Error during cleanup: {e}")
            # Continue with the test even if cleanup fails
            db_session.rollback()
            
        print("Cleanup completed")
    
    def test_timestamps_creation(self, db_session):
        """Test that created_at and updated_at are automatically set."""
        print("\n=== Starting test_timestamps_creation ===")
        
        # Define a model class inheriting from Base
        class TimestampTestModel(Base):
            id = Column(Integer, primary_key=True)
            name = Column(String(50))
        
        print("Model class defined")
        
        # Create the tables
        Base.metadata.create_all(bind=db_session.bind, tables=[TimestampTestModel.__table__])
        print(f"Tables created: {TimestampTestModel.__tablename__}")
        
        # Create a model instance
        now = datetime.utcnow()
        print(f"Current time before insert: {now}")
        
        test_model = TimestampTestModel(name="Test")
        db_session.add(test_model)
        print("Model instance added to session")
        
        db_session.commit()
        print(f"Commit completed. Model ID: {test_model.id}")
        print(f"Model timestamps after commit: created_at={test_model.created_at}, updated_at={test_model.updated_at}")
        
        # Retrieve the model from DB
        db_model = db_session.query(TimestampTestModel).filter(
            TimestampTestModel.name == "Test"
        ).first()
        print(f"Retrieved model from DB. Model ID: {db_model.id}")
        
        # Check timestamps
        print(f"DB model timestamps: created_at={db_model.created_at}, updated_at={db_model.updated_at}")
        assert db_model.created_at is not None
        assert db_model.updated_at is not None
        
        # created_at should be close to now
        diff = abs((db_model.created_at - now).total_seconds())
        print(f"Time difference: {diff} seconds")
        assert diff < 5  # within 5 seconds
        
        # Clean up - use safer approach to clean up
        print("Starting cleanup...")
        try:
            # Close the current session explicitly
            db_session.close()
            print("Session closed")
            
            # Drop using SQL execute instead of direct table drop
            db_session.execute(f"DROP TABLE IF EXISTS {TimestampTestModel.__tablename__}")
            db_session.commit()
            print("Table dropped via SQL command")
        except Exception as e:
            print(f"Error during cleanup: {e}")
            # Continue with the test even if cleanup fails
            db_session.rollback()
            
        print("Cleanup completed")
    
    def test_updated_at_updates(self, db_session):
        """Test that updated_at automatically updates when the model is updated."""
        print("\n=== Starting test_updated_at_updates ===")
        
        # Define a model class inheriting from Base
        class UpdateTestModel(Base):
            id = Column(Integer, primary_key=True)
            name = Column(String(50))
        
        # Create the tables
        Base.metadata.create_all(bind=db_session.bind, tables=[UpdateTestModel.__table__])
        print(f"Tables created: {UpdateTestModel.__tablename__}")
        
        # Create a model instance
        test_model = UpdateTestModel(name="Original")
        db_session.add(test_model)
        db_session.commit()
        print(f"Initial model created with ID: {test_model.id}")
        
        # Get the created_at and updated_at time
        original_created_at = test_model.created_at
        original_updated_at = test_model.updated_at
        print(f"Original timestamps: created_at={original_created_at}, updated_at={original_updated_at}")
        
        # Wait a bit to ensure time difference
        sleep(1)
        print("Waited 1 second")
        
        # Update the model
        test_model.name = "Updated"
        db_session.commit()
        print("Model updated and committed")
        
        # Retrieve the model from DB
        db_model = db_session.query(UpdateTestModel).filter(
            UpdateTestModel.name == "Updated"
        ).first()
        print(f"Retrieved updated model from DB with ID: {db_model.id}")
        print(f"Updated timestamps: created_at={db_model.created_at}, updated_at={db_model.updated_at}")
        
        # created_at should remain the same
        assert db_model.created_at == original_created_at
        
        # updated_at should be updated
        assert db_model.updated_at > original_updated_at
        print(f"Verified that updated_at changed: {original_updated_at} -> {db_model.updated_at}")
        
        # Clean up - use safer approach to clean up
        print("Starting cleanup...")
        try:
            # Close the current session explicitly
            db_session.close()
            print("Session closed")
            
            # Drop using SQL execute instead of direct table drop
            db_session.execute(f"DROP TABLE IF EXISTS {UpdateTestModel.__tablename__}")
            db_session.commit()
            print("Table dropped via SQL command")
        except Exception as e:
            print(f"Error during cleanup: {e}")
            # Continue with the test even if cleanup fails
            db_session.rollback()
            
        print("Cleanup completed") 