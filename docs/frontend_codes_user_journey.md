## Question

For frontend, read the project and tell me the endoint of prontend and the logical flow as a user journy the logical flow in a user journey way and specifiy which file which fuction. For example: "When runing the front end, what happen. Which file and function it run first, then which lead to which file and function. I want to know frontend code logic flow that corresponding to web UI user's journey. From home page to login to create chat to submit the first message to display assistant (AI) message to user configuration to logout, etc.

I'll explore the frontend codebase to understand the user journey flow and trace through the files and functions involved in each step.

Ran tool
Let me explore more about the dashboard, chat components, and the main user journey flow.

Read file: frontend/pages/_app.tsx

Ran tool

Ran tool

Ran tool

Ran tool

Ran tool

Ran tool

Ran tool

Ran tool
Based on my exploration of the codebase, I can now provide a detailed user journey flow of the frontend application:


# Frontend User Journey and Code Flow

## Endpoint
The frontend connects to a backend API at `http://localhost:8000/api/v1` (configurable through environment variables).

## Initial Load
1. **Entry Point**: `_app.tsx`
   - This is the first file that loads in the Next.js application
   - Sets up the application with global styles and toast notifications

2. **Home Page**: `pages/index.tsx`
   - The landing page users first see (`/`)
   - Contains links to login and register pages
   - Uses `Layout.tsx` component for page structure

## Authentication Flow

3. **Registration**: `pages/register.tsx` → `components/Auth/RegisterForm.tsx`
   - User clicks "Sign Up" button on home page
   - Navigates to `/register` route
   - `RegisterForm` component handles:
     - Form data collection (email, username, password, full name)
     - Form validation
     - API submission via `authApi.register()` from `lib/api.ts`
     - Success redirects to login page

4. **Login**: `pages/login.tsx` → `components/Auth/LoginForm.tsx`
   - User enters credentials on the login form
   - `LoginForm` component handles:
     - Form submission via `authApi.login()` from `lib/api.ts`
     - Stores JWT token in localStorage
     - Upon success, redirects to `/dashboard`

## Main Application Flow

5. **Dashboard**: `pages/dashboard.tsx`
   - After login, users land here
   - Protected route (checks for token in localStorage)
   - Has two main sections:
     - Left sidebar: Chat list
     - Right area: Active chat or empty state
   - On load, it calls `chatApi.getChats()` to fetch user's chat history
   - Key functions:
     - `handleNewChat()`: Creates a new chat
     - `handleLogout()`: Clears token and redirects to login page

6. **Chat Interaction**: `components/ChatUI.tsx`
   - Displayed when a chat is selected in the dashboard
   - Manages:
     - Chat message display with ReactMarkdown
     - Message input form
     - Message submission via `handleSubmit()`
     - `chatApi.streamChat()` for streaming responses from the AI
     - Auto-scrolling to newest messages

## Missing User Settings/Profile Page

The codebase does not appear to have a dedicated settings or profile page implemented yet, even though there are API endpoints prepared for it:
- `authApi.me()`: Fetch user profile
- `authApi.updateProfile()`: Update user profile
- `configApi.getUserConfig()`: Get user configuration
- `configApi.updateUserConfig()`: Update user preferences

## Complete User Journey Flow

1. User visits homepage (index.tsx)
2. User clicks "Sign Up" → Goes to register page (register.tsx) → Fills RegisterForm
3. User registers successfully → Redirected to login page (login.tsx)
4. User logs in via LoginForm → JWT token stored in localStorage
5. User redirected to dashboard (dashboard.tsx)
6. Dashboard loads:
   - Fetches chat history (`chatApi.getChats()`)
   - Displays chat list in sidebar
   - Sets first chat as active if available
7. User interacts with dashboard:
   - Create new chat (`handleNewChat()`)
   - Select existing chat (`setCurrentChat()`)
8. When chat is selected, ChatUI component renders:
   - Displays existing messages
   - Provides message input form
9. User sends a message:
   - Message added to UI
   - Request sent via `chatApi.streamChat()`
   - AI response displayed with streaming
10. User can log out (`handleLogout()`) → Redirected to login page

There is no dedicated profile or settings page implemented in the current codebase, although the API endpoints for those features exist in the API client.
