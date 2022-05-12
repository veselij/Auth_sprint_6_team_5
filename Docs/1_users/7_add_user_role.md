```mermaid
sequenceDiagram
    participant C as Client  
    participant S as Auth Server
    participant R as Redis

	Note over C, S: Add role to user
	C->>S: https://x.x.x.x/users/{user_id}/roles
	S->>S: check uuid from jwt same as in query if not is super user and token valid
	S-->>C: 401 Unauthorized
	S->>S: Add role to user
	S-->>C: Not Found (404)
	alt if uuid_query=jwt_uuid
	S->>R: delete refresh token, put access token to disabled table
	S->>S: generate new tokens (access & refresh)
	S->>R: store {user_id: refresh token}
	else if superuser
	S->>S: get access token from request
	S->>R: get refresh token for user
	end
	S->>C: OK(200) (access & refresh tokens)

```

**Path**: /users/{user_uuid}/roles

**Type**: POST
**Header**: Authorization: Bearer {token}  
**Body**: 
```
{
	"role_id": [1,2,3]
}
```
**Response Body**: 
```
{  
	"access_id": "access_token",
	"refresh_id": "refresh_token"
}  
```

Token time to live 1 day
Token refresh time to live 10 days

If superuser add role to user - user will get new role only after token refresh (mainly after expire time)