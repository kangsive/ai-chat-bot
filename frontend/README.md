# AI Chatbot Frontend

This is the frontend application for the AI Chatbot, refactored to use Next.js App Router.

## Technologies Used

- **Next.js 14** with App Router
- **React 18** with functional components and hooks
- **TypeScript** for type safety
- **Tailwind CSS** for styling
- **React Hot Toast** for notifications
- **React Markdown** for rendering markdown content
- **React Icons** for UI icons
- **Axios** for API requests
- **js-cookie** for cookie management

## Folder Structure

```
frontend/
├── app/                    # Next.js App Router directory
│   ├── auth/               # Authentication pages
│   │   ├── login/          # Login page
│   │   ├── register/       # Registration page
│   │   ├── reset-password/ # Password reset pages
│   │   └── verify-email/   # Email verification page
│   ├── dashboard/          # Dashboard page
│   ├── settings/           # User settings page
│   ├── components/         # Shared components
│   ├── lib/                # Utility functions and API services
│   ├── globals.css         # Global styles
│   ├── layout.tsx          # Root layout
│   └── page.tsx            # Home page
├── public/                 # Static assets
└── ... (config files)
```

## Features

- **Authentication System**: Login, registration, email verification, and password reset
- **Dashboard**: Chat management with conversation history
- **Chat Interface**: Streaming API integration for real-time AI responses
- **User Settings**: Profile management, AI preferences, security settings
- **Responsive Design**: Mobile-friendly interface
- **Protected Routes**: Middleware for route protection

## User Configuration

The user settings page allows customization of:

- **App Appearance**: Theme selection (light/dark/system)
- **Language Preferences**: UI language selection
- **AI Model Selection**: Choose between different LLM models
- **Response Settings**: Customize AI response length and tone
- **Notifications**: Enable/disable system notifications

## Authentication Flow

1. **Registration**: User creates an account with email, username, and password
2. **Email Verification**: User verifies email via link sent to their inbox
3. **Login**: User authenticates with username/email and password
4. **Password Reset**: Self-service password reset via email link

## API Integration

The frontend connects to the backend API via RESTful endpoints with JWT authentication.

## Getting Started

1. Clone the repository
2. Install dependencies:
   ```bash
   npm install
   ```
3. Set up environment variables (create a `.env.local` file):
   ```
   NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1
   ```
4. Run the development server:
   ```bash
   npm run dev
   ```
5. Open [http://localhost:3000](http://localhost:3000) in your browser

## Production Build

```bash
npm run build
npm start
```

## Docker Deployment

A Dockerfile is included for containerized deployment:

```bash
docker build -t ai-chatbot-frontend .
docker run -p 3000:3000 ai-chatbot-frontend
``` 