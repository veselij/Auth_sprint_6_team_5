```mermaid
sequenceDiagram
    participant C as Client  
    participant S as Auth Server
    participant R as Redis

	Note over C, S: logout
	C->>S: https://x.x.x.x/users/logout/{user_id}
	S->>S: check uuid from jwt with uuid in query or super_user if not match & check jwt signature
	S-->>C: 401 Unauthorized
	S->>R: delete {user_id: refresh token}
	S->>R: if not superuser put {user_id: access token} in canceled tokens table
	S->>C: OK(200)
```

**Path**: /users/logout/{user_id}  
**Type**: Post  
**Header**: Authorization: Bearer {token}  
**Body**: None  
**Response Body**: None  
