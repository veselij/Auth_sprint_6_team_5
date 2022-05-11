```mermaid
sequenceDiagram
    participant C as Client  
    participant S as Auth Server
    participant R as Redis

	Note over C, S: login
	C->>S: https://x.x.x.x/users/authenticate
	S->>S: Authentication
	Note right of S: check hash(passwd) with passwd in DB (using dynamic salt)
	S-->>C: 401 Unauthorized / 404 Not Found
	S->>S: generate tokens (access & refresh)
	S->>R: store {user_id: refresh token}
	S->>C: OK(200) (access & refresh tokens)
```

**Path**: /users/authenticate
**Type**: Post
**Body**:
{
	login: "",
	password: ""
}
**Response Body**:
{
access_id: access_token,
refresh_id: refresh_token
}

Token time to live 1 day
Token refresh time to live 10 days