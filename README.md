# AI Chatbot Application

A full-stack AI chatbot application with a FastAPI backend and Next.js frontend, using PostgreSQL for data storage and integrating with LLM APIs.

## Features

- **User Authentication**
  - Login/Register/Logout
  - Email verification (mock implementation)
  - Password reset (mock implementation)
  - JWT-based authentication
  - Login audit logging

- **Chat Capabilities**
  - Create and manage chat conversations
  - Stream responses from LLM
  - Chat history saved in database

- **Security**
  - Secure password hashing
  - Protected API endpoints
  - CORS configuration

## Tech Stack

### Backend
- **FastAPI**: High-performance Python web framework
- **SQLAlchemy**: SQL toolkit and ORM
- **PostgreSQL**: Relational database
- **Pydantic**: Data validation and settings management
- **JWT**: Authentication 
- **Alembic**: Database migrations

### Frontend
- **Next.js**: React framework
- **TailwindCSS**: Utility-first CSS framework
- **Vercel AI SDK**: For AI streaming and UI components
- **Axios**: HTTP client
- **React**: UI library

## Setup and Installation

### Prerequisites
- Docker and Docker Compose
- Node.js (for local frontend development)
- Python 3.10+ (for local backend development)

### Using Docker (Recommended)

1. Clone the repository
   ```
   git clone <repository-url>
   cd ai_chatbot_app
   ```

2. Create a `.env` file based on `.env.example`
   ```
   cp .env.example .env
   ```

3. Start the application using Docker Compose
   ```
   docker-compose up -d
   ```

4. Access the application
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:8000
   - API Documentation: http://localhost:8000/docs

### Local Development

#### Backend

1. Navigate to the backend directory
   ```
   cd backend
   ```

2. Create a virtual environment
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies
   ```
   pip install -r requirements.txt
   ```

4. Start the backend server
   ```
   <!-- cd ai_chatbot_app/backend
   alembic init -t generic alembic2
   cp alembic2/script.py.mako alembic/ && rm -rf alembic2 | cat

   # Created Alembic migration:
   alembic revision --autogenerate -m "create_tables" | cat

   # Apply the migration:
   alembic upgrade head | cat

   # Initialize the database:
   PYTHONPATH=$PWD python -m app.db.init_db | cat -->

   # Start the server
   uvicorn app.main:app --reload
   ```

#### Frontend

1. Navigate to the frontend directory
   ```
   cd frontend
   ```

2. Install dependencies
   ```
   npm install
   ```

3. Start the development server
   ```
   npm run dev
   ```

## Database Schema

The application uses the following core tables:

- **User**: Stores user account information
- **VerificationToken**: Email verification tokens
- **PasswordResetToken**: Password reset tokens
- **LoginAudit**: Authentication activity logging
- **Chat**: Chat conversation sessions
- **Message**: Individual messages in chats
- **UserConfig**: User-specific configuration
- **SystemConfig**: Global system configuration

## API Documentation

API documentation is available at `/docs` when running the backend.

## LLM Integration

The application includes a mock LLM implementation for demonstration purposes. To use a real LLM:

1. Update the LLM_API_KEY and LLM_MODEL environment variables
2. Modify the `generate_llm_response` function in `app/services/llm.py`

## License

[MIT License](LICENSE) 