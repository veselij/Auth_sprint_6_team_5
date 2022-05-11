```mermaid
sequenceDiagram
    participant C as Client  
    participant S as Auth Server
    participant R as Redis

	Note over C, S: Get user login history
	C->>S: https://x.x.x.x/users/history/{user_id}
	S->>S: check uuid from jwt with uuid in query or super user if not & check jwt signature
	S-->>C: 401 Unauthorized
	S->>S: change user data
	S->>S: update key3 if password was changed
	S->>S: generate new tokens (access & refresh)
	S->>R: delete exising refresh token for user_id
	S->>R: store {user_id: refresh token}
	S->>C: OK(200) History data
	
```

**Path**: /users/history/{user_id}?per_pagenum=x&page_num=y

**Type**: GET
**Header**: Authorization: Bearer {token}
**Body**: None
**Response Body**:
{
user_agent: "",
login_date: "",
login_status: ""
}