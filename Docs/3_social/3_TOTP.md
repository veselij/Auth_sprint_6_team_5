```mermaid
sequenceDiagram
	participant C as Client  
	participant S as Auth Server
	participant D as DataBase
	Note over C, S: Add TOTP to user
	C->>S: https://x.x.x.x/totp/sync
    S->>S: check token annd get user_id
	S-->>C: 401 Unauthorized
    S->>S: generate new secret key and provision url
    S->>D: add to user new secret key
    S->>C: send provision url to user (201)
```

**Path**: /totp/sync
**Type**: GET
**Header**: Authorization: Bearer {token}  
**Body**: None
**Response Body**
```
{
"totp_provisioning_url": ""
}
```

```mermaid
sequenceDiagram
	participant C as Client  
	participant S as Auth Server
	participant D as DataBase
	Note over C, S: Activate TOTP for user
	C->>S: https://x.x.x.x/totp/sync
    S->>S: check token and get user_id
	S-->>C: 401 Unauthorized
    S->>S: get code from request and check if it is valid
    S->>D: add to user flag TOTP activated
    S->>C: send (200)
```

**Path**: /totp/sync
**Type**: POST
**Header**: Authorization: Bearer {token}  
**Body**: 
```
{
    "code": ""
}
```
**Response Body**: None


```mermaid
sequenceDiagram
	participant C as Client  
	participant S as Auth Server
	participant R as Redis
	Note over C, S: Check TOTP for request
	C->>S: https://x.x.x.x/totp/check/<request_id>
    S->>R: check that request-id exists and get user_id and is_superuser and totp sync active status
	S-->>C: 401 Unauthorized
    S->>S: check that user has activated TOTP
	alt: TOTP active but not in sync
	S--XC: 401 Unauthorized
	else TOTP active and in sync sync:
    S->>S: get code from request and check if it is valid
	else TOTP not active:
	end
    S->>S: generate tokens (access & refresh & required fields)
	S->>R: store in db0 {refesh_token_id: user_id}
	S->>C: OK(200) (access & refresh tokens)
```

**Path**: /totp/check/<request_id>
**Type**: POST
**Body**: 
```
{
    "code": ""
}
```
**Response Body**:
```
{
	"access_token": "access_token",
	"refresh_token": "refresh_token",
	"required_fields": [],
}  
```