```mermaid
sequenceDiagram
	participant C as Client  
	participant S as Auth Server
	participant P as Provider
	Note over C, S: registration
	C->>S: https://x.x.x.x/users/register/social?provider=Enum[]
	S->>S: chouse right provider
	S->>P: redirect to Provider with required scope, code, ids
	P->>C: request login and password from Provider
	C->>P: send login, password etc
	P->>P: autorize and confirm scope
	P->>S: send token to redirect URL
	S->>P: ask for access_token
	S->>S: get user data from access_token
	opt if not user data in token
	S->>P: request user data with access token
	P->>S: user data
	end
	S->>S: check if Social account exists
	opt not exists
	S->>S: create social account and User
	end
	S->>S: generate request_id, required_fields
	S->>R: store in db2 request_id: user_id,required_fields, totp active, totp secret, totp-sync status, is_admin
	S->>C: OK(200) (request_id)
	end
```

**Path**: /users/register/social?provider=Enum[]  
**Type**: Get  
**Body**: None  
**Response Body**
```
{
	"request_id": ""
}
```