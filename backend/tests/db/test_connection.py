from sqlalchemy import create_engine, Column, Integer, String, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import os

# Test database URL
TEST_DATABASE_URL = os.environ.get(
    "TEST_DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/test_chatbot_db"
)

# Create engine and base
engine = create_engine(TEST_DATABASE_URL)
Base = declarative_base()


# Define a simple test model
class TestModel(Base):
    __tablename__ = "test_models"
    
    id = Column(Integer, primary_key=True)
    name = Column(String(50), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)


def main():
    """Test database connection and basic ORM operations"""
    print("Testing connection to:", TEST_DATABASE_URL)
    
    try:
        # Create all tables
        Base.metadata.create_all(engine)
        print("Tables created successfully")
        
        # Create a session
        Session = sessionmaker(bind=engine)
        session = Session()
        
        # Add a test record
        test_record = TestModel(name="Test Record")
        session.add(test_record)
        session.commit()
        print("Record added successfully, ID:", test_record.id)
        
        # Query the record
        retrieved_record = session.query(TestModel).filter_by(id=test_record.id).first()
        print(f"Retrieved record: ID={retrieved_record.id}, Name={retrieved_record.name}")
        
        # Clean up
        session.delete(retrieved_record)
        session.commit()
        print("Record deleted successfully")
        
        # Drop the table
        Base.metadata.drop_all(engine)
        print("Tables dropped successfully")
        
        print("All tests passed!")
        
    except Exception as e:
        print("Error:", e)
        

if __name__ == "__main__":
    main() 