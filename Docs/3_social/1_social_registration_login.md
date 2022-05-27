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
	S->>S: generate required_fields list and access and refresh tokens for Auth service
	S->>C: TokenScheme с access_toke & refesh_token & required_fields = list (200)
	Note left of C: front end logic
	opt required_fields not empty
	C->>S: change_user_data
	S->>C: OK(200)
	end
```

**Path**: /users/register/social?provider=Enum[]  
**Type**: Get  
**Body**: None  
**Response Body**
```
{
	"access_token": "access_token",
	"refresh_token": "refresh_token",
	"required_fields": list() #optional
}
```