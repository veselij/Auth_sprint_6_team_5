```mermaid
sequenceDiagram
    participant C as Client  
    participant S as Auth Server
    participant R as Redis

	Note over C, S: Get user data
	C->>S: https://x.x.x.x/users/{user_id}
	S->>S: check uuid from jwt with uuid in query or super user if not & check jwt signature
	S-->>C: 401 Unauthorized
	S->>S: get user data
	S->>C: OK(200) (user data)
	
```

**Path**: /users/{user_id} 

**Type**: Get  
**Header**: Authorization: Bearer {token}  
**Body**: None  
**Response Body**:  
```
{
	"first_name": "",
	"last_name": ""
}  
```

Token time to live 1 day
Token refresh time to live 10 days