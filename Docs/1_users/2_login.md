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
	S->>S: check if TOTP active
	S->>S: generate response
	S->>C: OK(200) (response)
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
  "request_id": "string",
  "token": {
    "access_token": "string",
    "refresh_token": "string",
    "required_fields": [
      "string"
    ]
  },
  "totp_active": true
}  
```
