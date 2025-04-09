# Inspect database
Test databaase connection:
```
psql -h localhost -U postgres -c "SELECT 1" | cat
```

or 
```
cd ai_chatbot_app/backend
python test_connection.py
```

Let's now check what databases exist:
```
psql -h localhost -U postgres -c "\l" | cat
```

I see the ai_chatbot database exists, but the test database test_chatbot_db doesn't exist yet. Let's create it:
```
psql -h localhost -U postgres -c "CREATE DATABASE test_chatbot_db;" | cat
```

Excellent! We've successfully created the test database. Now let's check if we can connect to it:
```
psql -h localhost -U postgres -d test_chatbot_db -c "SELECT 1" | cat
```

Query the database:
```
psql -h localhost -U postgres -d test_chatbot_db -c "SELECT * FROM users;" | cat
psql -h localhost -U postgres -d ai_chatbot -c "SELECT id, role, content_json FROM message LIMIT 10;" | cat
```

To remove a database:
```
psql -h localhost -U postgres -c "DROP DATABASE test_chatbot_db;" | cat
```

# Database migration
Now let's update the tables by running the database migration:
```
alembic stamp head # or python -m alembic stamp head
alembic upgrade head # or python -m alembic upgrade head
alembic revision --autogenerate -m "Changes Note" # or python -m alembic revision --autogenerate -m "Changes Note"
```
```
cd ai_chatbot_app/backend && alembic revision --autogenerate -m "Rename user table to users"
```
It seems we need to initialize the Alembic migrations first. Let's do that:
```
cd ai_chatbot_app/backend && alembic init alembic
```


Reset database:
```
# drop alembic_version table if it exists
psql -h localhost -U postgres -d ai_chatbot -c "DROP TABLE IF EXISTS alembic_version;" | cat

<!-- # reset alembic
cd ai_chatbot_app/backend && alembic reset -->

# reset database to the base state
alembic stamp base | cat

# delete all migration files and pycache
rm -f alembic/versions/*.py
rm -rf alembic/versions/__pycache__

# create a new initial migration
alembic revision --autogenerate -m "Initial migration" | cat

# recreate all tables
alembic upgrade head | cat

# verify all tables are created
psql -h localhost -U postgres -d ai_chatbot -c "\dt" | cat
```


