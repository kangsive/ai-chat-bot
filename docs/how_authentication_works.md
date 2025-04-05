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

## Question
If restart backend, will the token I got from last login still available? 

## Answer
No, the token will expire after a certain period of time. You will need to login again to get a new token.

## Question

When you restart the backend, the availability of the JWT (JSON Web Token) you received during your last login depends on how the token is being managed and stored.

### Key Points to Consider:

1. **Stateless Nature of JWTs**: 
   - JWTs are stateless, meaning they do not require server-side storage. Once issued, they can be used until they expire, regardless of the server's state. 

2. **Expiration**:
   - The token will remain valid until its expiration time, which is set when the token is created. In your code, the expiration is determined by the `ACCESS_TOKEN_EXPIRE_MINUTES` setting. If the token has not expired, it will still be valid after a backend restart.

3. **Token Storage**:
   - If the token is stored client-side (e.g., in local storage or cookies), it will still be available to the client after a backend restart. The client can continue to use the token for authentication until it expires.

4. **Revocation**:
   - If you have implemented a mechanism to revoke tokens (e.g., maintaining a blacklist of tokens), then a restart might affect that mechanism depending on how it is implemented. If the blacklist is stored in memory and not persisted, it will be cleared on restart.

### Conclusion:
When you restart the backend, the availability of the JWT (JSON Web Token) you received during your last login depends on how the token is being managed and stored.

1. Stateless Nature of JWTs:
   - JWTs are stateless, meaning they do not require server-side storage. Once issued, they can be used until they expire, regardless of the server's state.

2. Expiration:
   - The token will remain valid until its expiration time, which is set when the token is created. In your code, the expiration is determined by the ACCESS_TOKEN_EXPIRE_MINUTES setting. If the token has not expired, it will still be valid after a backend restart.
  
3. Token Storage:
   - If the token is stored client-side (e.g., in local storage or cookies), it will still be available to the client after a backend restart. The client can continue to use the token for authentication until it expires.

4. Revocation:
   - If you have implemented a mechanism to revoke tokens (e.g., maintaining a blacklist of tokens), then a restart might affect that mechanism depending on how it is implemented. If the blacklist is stored in memory and not persisted, it will be cleared on restart.

If your backend simply restarts and the token has not expired, it will still be valid for authentication. However, if you have a revocation mechanism that relies on in-memory storage, that may affect the token's validity after a restart.

## Question
But when in localhost:8000/docs when I refresh browser and test users/me endpoint again I got {
  "detail": "Not authenticated"
}?

## Answer
If the token is stored in the browser (e.g., in local storage or cookies), ensure that it is still present after refreshing the page. If the token is lost or not sent with the request, you will receive an authentication error.



