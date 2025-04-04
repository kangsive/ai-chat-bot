"""
Database Validation Summary Script

This script verifies all the key aspects of the database setup:
1. Connection to the PostgreSQL server
2. Existence of the test database
3. Ability to create tables and perform CRUD operations
"""

import os
import sys
from sqlalchemy import create_engine, inspect, Column, Integer, String, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime

# Test database URL
TEST_DATABASE_URL = os.environ.get(
    "TEST_DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/test_chatbot_db"
)

# Default PostgreSQL URL (for checking server connection)
DEFAULT_PG_URL = "postgresql://postgres:postgres@localhost:5432/postgres"

def check_server_connection():
    """Check connection to PostgreSQL server"""
    try:
        engine = create_engine(DEFAULT_PG_URL)
        conn = engine.connect()
        conn.close()
        print("✅ Successfully connected to PostgreSQL server")
        return True
    except Exception as e:
        print("❌ Failed to connect to PostgreSQL server:")
        print(f"   Error: {e}")
        return False

def check_test_db_exists():
    """Check if test database exists"""
    try:
        # Connect to default postgres database
        engine = create_engine(DEFAULT_PG_URL)
        inspector = inspect(engine)
        
        # Get list of databases
        conn = engine.connect()
        result = conn.execute("SELECT datname FROM pg_database;")
        databases = [row[0] for row in result]
        conn.close()
        
        # Check if our test database exists
        test_db_name = TEST_DATABASE_URL.split('/')[-1]
        if test_db_name in databases:
            print(f"✅ Test database '{test_db_name}' exists")
            return True
        else:
            print(f"❌ Test database '{test_db_name}' does not exist")
            return False
    except Exception as e:
        print("❌ Failed to check test database existence:")
        print(f"   Error: {e}")
        return False

def create_test_db_if_not_exists():
    """Create test database if it doesn't exist"""
    try:
        # Connect to default postgres database
        engine = create_engine(DEFAULT_PG_URL)
        
        # Get test database name
        test_db_name = TEST_DATABASE_URL.split('/')[-1]
        
        # Check if test database exists
        conn = engine.connect()
        conn.execute("COMMIT")  # Close any open transactions
        result = conn.execute(f"SELECT 1 FROM pg_database WHERE datname='{test_db_name}'")
        exists = result.fetchone() is not None
        
        if not exists:
            # Create the database
            conn.execute("COMMIT")
            conn.execute(f'CREATE DATABASE {test_db_name}')
            print(f"✅ Created test database '{test_db_name}'")
        else:
            print(f"ℹ️ Test database '{test_db_name}' already exists")
        
        conn.close()
        return True
    except Exception as e:
        print("❌ Failed to create test database:")
        print(f"   Error: {e}")
        return False

def test_db_operations():
    """Test basic database operations"""
    try:
        # Create engine and base
        engine = create_engine(TEST_DATABASE_URL)
        Base = declarative_base()
        
        # Define a test model
        class TestModel(Base):
            __tablename__ = "test_db_validation"
            
            id = Column(Integer, primary_key=True)
            name = Column(String(50), nullable=False)
            timestamp = Column(DateTime, default=datetime.utcnow)
            
        # Create table
        Base.metadata.create_all(engine)
        print("✅ Successfully created table in test database")
        
        # Create session
        Session = sessionmaker(bind=engine)
        session = Session()
        
        # Insert record
        test_record = TestModel(name="Test Record")
        session.add(test_record)
        session.commit()
        print(f"✅ Successfully inserted record (ID: {test_record.id})")
        
        # Query record
        retrieved = session.query(TestModel).filter_by(id=test_record.id).first()
        if retrieved and retrieved.name == "Test Record":
            print("✅ Successfully retrieved record")
        else:
            print("❌ Failed to retrieve record correctly")
        
        # Update record
        retrieved.name = "Updated Record"
        session.commit()
        updated = session.query(TestModel).filter_by(id=test_record.id).first()
        if updated and updated.name == "Updated Record":
            print("✅ Successfully updated record")
        else:
            print("❌ Failed to update record")
        
        # Delete record
        session.delete(updated)
        session.commit()
        deleted = session.query(TestModel).filter_by(id=test_record.id).first()
        if deleted is None:
            print("✅ Successfully deleted record")
        else:
            print("❌ Failed to delete record")
        
        # Drop table
        Base.metadata.drop_all(engine)
        print("✅ Successfully dropped table")
        
        return True
    except Exception as e:
        print("❌ Error during database operations test:")
        print(f"   Error: {e}")
        return False

def main():
    """Run all database validation checks"""
    print("\n=== DATABASE VALIDATION SUMMARY ===\n")
    
    # Step 1: Check PostgreSQL server connection
    if not check_server_connection():
        print("\n❌ DATABASE VALIDATION FAILED: Cannot connect to PostgreSQL server")
        sys.exit(1)
    
    # Step 2: Check if test database exists
    db_exists = check_test_db_exists()
    
    # Step 3: Create test database if it doesn't exist
    if not db_exists:
        if not create_test_db_if_not_exists():
            print("\n❌ DATABASE VALIDATION FAILED: Could not create test database")
            sys.exit(1)
    
    # Step 4: Test database operations
    if not test_db_operations():
        print("\n❌ DATABASE VALIDATION FAILED: Database operations test failed")
        sys.exit(1)
    
    print("\n✅ DATABASE VALIDATION SUCCESSFUL")
    print("All checks passed. Your database is configured correctly for testing.")
    print(f"Test database URL: {TEST_DATABASE_URL}")

if __name__ == "__main__":
    main() 