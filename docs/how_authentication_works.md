## Question:
 In localhost:8000/docs, I'm testing the read_user_me endpoint. from my understanding I need to login to get acesstoken. But I don't get where it is used, I see in get_current_uder function it depends on oauth2_schema pointing to login url. But how is credential information pass to here? Explain me the overview how authenciation works.

## Answer:
I'll explain how the authentication flow works in your FastAPI app:

1. When you access `/docs`, you see the Swagger UI where you can test endpoints.

2. The authentication flow follows these steps:

   - Your `read_user_me` endpoint depends on `get_current_active_user`, which depends on `get_current_user`.
   
   - The `get_current_user` function depends on the `oauth2_scheme`, which is an OAuth2PasswordBearer pointing to your login endpoint.

3. Authentication process:

   - First, you need to call the `/login` endpoint, providing username/email and password.
   
   - The login endpoint authenticates your credentials, creates an access token, and returns it.
   
   - In Swagger UI, click "Authorize" button (top-right) and enter this token (or login with username/password and get token from login endpoint automatically).
   
   - For subsequent requests, Swagger will automatically include the token in the Authorization header. (If you are using postman, you need to add the token in the Authorization header manually.)

4. Behind the scenes:

   - The `oauth2_scheme` extracts the token from the incoming request's Authorization header. When used as a dependency, OAuth2PasswordBearer extracts the token from the Authorization header of the current request.Parameter tokenUrl=f"{settings.API_V1_STR}/users/login" tells OpenAPI/Swagger UI where users should go to obtain tokens which is purely for documentation/UI purposes.
   
   - `get_current_user` receives this token, validates it, and retrieves the user.
   
   - `get_current_active_user` checks if the user is active.
   
   - Finally, `read_user_me` receives the authenticated user and returns it.

To test in Swagger UI:
1. Execute the `/login` endpoint with valid credentials
2. Copy the access token from the response
3. Click "Authorize" and paste "Bearer YOUR_TOKEN" 
4. Now you can test protected endpoints like `/me`
