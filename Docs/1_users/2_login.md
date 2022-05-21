```mermaid
sequenceDiagram
    participant C as Client  
    participant S as Auth Server
    participant R as Redis

	Note over C, S: login
	C->>S: https://x.x.x.x/users/login
	S->>S: Authentication
	Note right of S: check hash(passwd) with passwd in DB (using dynamic salt)
	S-->>C: 401 Unauthorized
	S->>S: generate tokens (access & refresh)
	S->>R: store in db0 {refesh_token_id: user_id}
	S->>C: OK(200) (access & refresh tokens)
```

**Path**: /users/login
**Type**: Post  
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
	"access_token": "access_token",
	"refresh_token": "refresh_token"
}  
```
Token time to live 1 day
Token refresh time to live 10 days
