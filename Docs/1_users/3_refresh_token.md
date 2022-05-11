```mermaid
sequenceDiagram
    participant C as Client  
    participant S as Auth Server
    participant R as Redis

	Note over C, S: Refresh token
	C->>S: https://x.x.x.x/users/refresh/{user_id}
	S->>S: check uuid from jwt with uuid in query or super user if not & check jwt signature
	S-->>C: 401 Unauthorized
	S->>R: Check if refresh token valid for this uuid
	S-->>C: 401 Unauthorized
	S->>S: generate new tokens (access & refresh)
	S->>R: store {user_id: refresh token}
	S->>C: OK(200) (access & refresh tokens)
	
```

**Path**: /users/refresh/{user_id}  

**Type**: Get  
**Header**: Authorization: Bearer {token}  
**Body**: None  
**Response Body**:  
{  
access_id: access_token,
refresh_id: refresh_token
}  

Token time to live 1 day
Token refresh time to live 10 days
