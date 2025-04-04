# Database Tests

This directory contains tests for the database models of the AI Chatbot application.

## Structure

- `conftest.py`: Contains pytest fixtures for database testing
- `models/`: Tests for the database models
  - `test_base_model.py`: Tests for the Base model functionality
  - `test_user_model.py`: Tests for the User model and related entities
  - `test_chat_model.py`: Tests for the Chat and Message models
  - `test_config_model.py`: Tests for the UserConfig and SystemConfig models

## Running Tests

To run the database tests, make sure you have a PostgreSQL server running and create a test database:

```bash
# Start docker container with postgres
docker compose up db -d

# Install psql
sudo apt-get install postgresql-client

# Inspect database
psql -h localhost -U postgres -c "SELECT 1" | cat # Check connection to postgres server
psql -h localhost -U postgres -c "\l" | cat # Check existing databases
psql -h localhost -U postgres -c "CREATE DATABASE test_chatbot_db;" | cat # Create test database
# Create test database
 # Skip if database already exists

# Run the tests
cd ai_chatbot_app/backend
pytest -v tests/models/

# Test a single file
pytest -v tests/models/test_user_model.py

# Run a specific test function with print by adding -s
python -m pytest tests/models/test_base_model.py::TestBaseModel::test_timestamps_creation -v -s
```

## Test Database Configuration

The tests use a separate test database to avoid affecting your development or production data. The test database connection is configured in `conftest.py`.

By default, the tests use the following database URL:
```
postgresql://postgres:postgres@localhost:5432/test_chatbot_db
```

You can override this by setting the `TEST_DATABASE_URL` environment variable.

## Test Isolation

Each test function runs with its own isolated database session. The database tables are created before each test and dropped after each test, ensuring that tests don't affect each other.

## Adding New Tests

When adding new models to the application, please create corresponding test files in the `tests/models/` directory following the existing patterns. 