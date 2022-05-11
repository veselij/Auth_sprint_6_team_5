```mermaid
sequenceDiagram
    participant C as Client  
    participant S as Auth Server
    participant R as Redis

	Note over C, S: Change user data
	C->>S: https://x.x.x.x/users/{user_id}
	S->>S: check uuid from jwt with uuid in query or super user if not & check jwt signature
	S-->>C: 401 Unauthorized
	S->>S: change user data
	S->>S: update key3 if password was changed
	S->>S: generate new tokens (access & refresh)
	S->>R: delete exising refresh token for user_id
	S->>R: store {user_id: refresh token}
	S->>C: OK(200) (access & refresh tokens)
	
```

**Path**: /users/{user_id}  
**Type**: PUT  
**Header**: Authorization: Bearer {token}  
**Body**:   
{
	first_name: "",
	last_name: "",
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
