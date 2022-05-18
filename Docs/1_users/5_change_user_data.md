```mermaid
sequenceDiagram
    participant C as Client  
    participant S as Auth Server
    participant R as Redis

	Note over C, S: Change user data
	C->>S: https://x.x.x.x/users/{user_id}
	S->>S: check uuid from jwt with uuid in query or super user if not & check jwt signature
	S-->>C: 401 Unauthorized
	S->>S: check if new login not exist
	S-->>C: Conflict (409)
	S->>S: change user data
	S->>C: OK(200)
	
```

**Path**: /users/{user_id}  
**Type**: PUT  
**Header**: Authorization: Bearer {token}  
**Body**:
```
{
	"login": "",
	"password": ""
}  
```
**Response Body**:  
```
{
	"access_id": "access_token,
	"refresh_id": "refresh_token"
}  
```