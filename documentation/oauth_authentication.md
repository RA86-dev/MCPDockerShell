# MCP Docker Server OAuth 2.1 Authentication

This document explains how to set up and use OAuth 2.1 authentication with the MCP Docker Server, following the MCP OAuth specification.

## Overview

The MCP Docker Server implements OAuth 2.1 with full MCP specification compliance, providing:

- **Authorization Server Discovery** (RFC 8414)
- **Protected Resource Metadata** (RFC 9728) 
- **Dynamic Client Registration** (RFC 7591)
- **PKCE Support** (RFC 7636)
- **Resource Indicators** (RFC 8707)
- **Token Audience Binding** for security

## Quick Setup

### 1. Enable OAuth in Docker Compose

Edit your `compose.yml` and set:

```yaml
environment:
  - ENABLE_MCP_OAUTH=true
  - MCP_OAUTH_REQUIRE_AUTH=true  # Require auth for protected resources
```

### 2. Start the Server

```bash
docker-compose up -d
```

### 3. Verify OAuth Endpoints

Check that OAuth endpoints are working:

```bash
# Protected Resource Metadata (RFC 9728)
curl http://localhost:8000/.well-known/oauth-protected-resource

# Authorization Server Metadata (RFC 8414)  
curl http://localhost:8000/.well-known/oauth-authorization-server

# OpenID Connect Discovery
curl http://localhost:8000/.well-known/openid-configuration
```

## OAuth 2.1 Flow Implementation

### Step 1: Authorization Server Discovery

The client discovers the authorization server using Protected Resource Metadata:

```bash
# Client makes request without token
curl http://localhost:8000/oauth/test

# Server responds with 401 and WWW-Authenticate header
# WWW-Authenticate: Bearer resource="http://localhost:8000/.well-known/oauth-protected-resource"

# Client fetches resource metadata
curl http://localhost:8000/.well-known/oauth-protected-resource
```

### Step 2: Client Registration (Optional)

If using dynamic registration:

```bash
curl -X POST http://localhost:8000/oauth/register \
  -H "Content-Type: application/json" \
  -d '{
    "client_name": "My MCP Client",
    "redirect_uris": ["http://localhost:3000/callback"],
    "grant_types": ["authorization_code", "refresh_token"],
    "response_types": ["code"]
  }'
```

### Step 3: Authorization Request

Generate PKCE parameters and request authorization:

```python
import secrets, hashlib, base64

# Generate PKCE parameters
code_verifier = base64.urlsafe_b64encode(secrets.token_bytes(32)).decode().rstrip('=')
code_challenge = base64.urlsafe_b64encode(
    hashlib.sha256(code_verifier.encode()).digest()
).decode().rstrip('=')

# Authorization URL
auth_url = f"http://localhost:8000/oauth/authorize?" \
           f"client_id=mcp-docker-server-default&" \
           f"response_type=code&" \
           f"redirect_uri=http://localhost:3000/callback&" \
           f"code_challenge={code_challenge}&" \
           f"code_challenge_method=S256&" \
           f"resource=http://localhost:8000&" \
           f"scope=mcp:read mcp:write&" \
           f"state=random-state-value"
```

### Step 4: Token Exchange

Exchange authorization code for access token:

```bash
curl -X POST http://localhost:8000/oauth/token \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "grant_type=authorization_code" \
  -d "code=AUTHORIZATION_CODE" \
  -d "redirect_uri=http://localhost:3000/callback" \
  -d "code_verifier=CODE_VERIFIER" \
  -d "client_id=mcp-docker-server-default"
```

### Step 5: Access Protected Resources

Use the access token to access protected resources:

```bash
curl http://localhost:8000/oauth/test \
  -H "Authorization: Bearer ACCESS_TOKEN"
```

## Configuration Options

All OAuth configuration is done via environment variables in `compose.yml`:

```yaml
environment:
  # Basic OAuth Settings
  - ENABLE_MCP_OAUTH=true
  - MCP_OAUTH_REQUIRE_AUTH=true
  
  # Server Configuration
  - MCP_OAUTH_AUTHORIZATION_SERVER=http://mcp-server:8000
  - MCP_OAUTH_ISSUER=http://mcp-server:8000
  - MCP_OAUTH_RESOURCE_URI=http://mcp-server:8000
  
  # Client Credentials (for pre-registered clients)
  - MCP_OAUTH_CLIENT_ID=mcp-docker-server-default
  - MCP_OAUTH_CLIENT_SECRET=mcp_secret_key_change_in_production_2024
  - MCP_OAUTH_CLIENT_NAME="MCP Docker Dev Server"
  
  # Token Configuration
  - MCP_OAUTH_TOKEN_EXPIRY=3600  # 1 hour
  - MCP_OAUTH_SCOPE=mcp:read mcp:write mcp:admin
  
  # Security Features
  - MCP_OAUTH_REQUIRE_HTTPS=false  # Set true in production
  - MCP_OAUTH_DYNAMIC_REGISTRATION=true
  - MCP_OAUTH_ENABLE_PKCE=true
```

## Available OAuth Endpoints

### Well-Known Endpoints

- `/.well-known/oauth-protected-resource` - Protected Resource Metadata (RFC 9728)
- `/.well-known/oauth-authorization-server` - Authorization Server Metadata (RFC 8414)
- `/.well-known/openid-configuration` - OpenID Connect Discovery
- `/.well-known/jwks.json` - JSON Web Key Set

### OAuth Flow Endpoints

- `/oauth/authorize` - Authorization endpoint with PKCE support
- `/oauth/token` - Token endpoint with PKCE verification
- `/oauth/register` - Dynamic client registration (RFC 7591)
- `/oauth/userinfo` - User information endpoint

### Test Endpoints

- `/oauth/test` - Protected test endpoint to verify authentication

## MCP Tools for OAuth Management

The server provides MCP tools for OAuth management:

- `mcp_oauth_protected_resource_metadata` - Get protected resource metadata
- `mcp_oauth_authorization_server_metadata` - Get authorization server metadata  
- `mcp_oauth_validate_token` - Validate access tokens
- `mcp_oauth_get_configuration` - Get OAuth configuration
- `mcp_oauth_register_client` - Register OAuth clients dynamically
- `mcp_oauth_check_compliance` - Check MCP specification compliance

## Security Considerations

### Production Deployment

1. **Use HTTPS**: Set `MCP_OAUTH_REQUIRE_HTTPS=true`
2. **Strong Secrets**: Change `MCP_OAUTH_CLIENT_SECRET` to a strong value
3. **Restrict CORS**: Configure `allow_origins` appropriately 
4. **Secure JWT Keys**: Use proper key management for JWT signing

### Token Security

- **Audience Binding**: Tokens are bound to specific resource servers
- **Short Expiry**: Access tokens expire in 1 hour by default
- **No Token Passthrough**: Tokens are validated, never passed through
- **PKCE Required**: All authorization flows require PKCE

### Client Security

- **Dynamic Registration**: Clients can register automatically
- **Redirect URI Validation**: Exact match validation prevents attacks
- **State Parameter**: Always use state parameter to prevent CSRF

## Testing OAuth Flow

### Using curl

```bash
# 1. Test protected endpoint (should get 401)
curl -v http://localhost:8000/oauth/test

# 2. Get protected resource metadata
curl http://localhost:8000/.well-known/oauth-protected-resource

# 3. Register a client
curl -X POST http://localhost:8000/oauth/register \
  -H "Content-Type: application/json" \
  -d '{"client_name": "Test Client", "redirect_uris": ["http://localhost:8080/callback"]}'

# 4. Generate PKCE and visit authorization URL in browser
# http://localhost:8000/oauth/authorize?client_id=CLIENT_ID&response_type=code&redirect_uri=http://localhost:8080/callback&code_challenge=CHALLENGE&code_challenge_method=S256

# 5. Exchange code for token
curl -X POST http://localhost:8000/oauth/token \
  -d "grant_type=authorization_code&code=AUTH_CODE&redirect_uri=http://localhost:8080/callback&code_verifier=VERIFIER&client_id=CLIENT_ID"

# 6. Use token to access protected resource
curl http://localhost:8000/oauth/test \
  -H "Authorization: Bearer ACCESS_TOKEN"
```

### Using MCP Tools

```bash
# Check OAuth compliance
mcp_oauth_check_compliance

# Validate a token
mcp_oauth_validate_token token="ACCESS_TOKEN" required_scopes="mcp:read"

# Get configuration
mcp_oauth_get_configuration
```

## Troubleshooting

### Common Issues

1. **OAuth disabled**: Ensure `ENABLE_MCP_OAUTH=true`
2. **Missing dependencies**: Check that `python-jose` and `authlib` are installed
3. **Invalid tokens**: Verify token audience matches resource server URI
4. **PKCE errors**: Ensure `code_challenge_method=S256` and valid verifier

### Debug Mode

Enable verbose logging:

```bash
docker-compose logs -f mcp-server
```

### Verify Installation

Check OAuth libraries are available:

```python
try:
    import jose
    import authlib
    print("OAuth libraries installed")
except ImportError as e:
    print(f"Missing OAuth libraries: {e}")
```

## Integration Examples

### Python Client Example

```python
import requests
import secrets
import hashlib
import base64

class MCPOAuthClient:
    def __init__(self, base_url="http://localhost:8000"):
        self.base_url = base_url
        self.access_token = None
    
    def get_authorization_url(self, client_id, redirect_uri, scope="mcp:read"):
        # Generate PKCE parameters
        self.code_verifier = base64.urlsafe_b64encode(
            secrets.token_bytes(32)
        ).decode().rstrip('=')
        
        code_challenge = base64.urlsafe_b64encode(
            hashlib.sha256(self.code_verifier.encode()).digest()
        ).decode().rstrip('=')
        
        # Build authorization URL
        params = {
            "client_id": client_id,
            "response_type": "code", 
            "redirect_uri": redirect_uri,
            "code_challenge": code_challenge,
            "code_challenge_method": "S256",
            "resource": self.base_url,
            "scope": scope,
            "state": secrets.token_urlsafe(16)
        }
        
        query_string = "&".join([f"{k}={v}" for k, v in params.items()])
        return f"{self.base_url}/oauth/authorize?{query_string}"
    
    def exchange_code_for_token(self, code, client_id, redirect_uri):
        data = {
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": redirect_uri, 
            "code_verifier": self.code_verifier,
            "client_id": client_id
        }
        
        response = requests.post(f"{self.base_url}/oauth/token", data=data)
        if response.status_code == 200:
            token_data = response.json()
            self.access_token = token_data["access_token"]
            return token_data
        else:
            raise Exception(f"Token exchange failed: {response.text}")
    
    def call_protected_resource(self, endpoint):
        if not self.access_token:
            raise Exception("No access token available")
        
        headers = {"Authorization": f"Bearer {self.access_token}"}
        response = requests.get(f"{self.base_url}{endpoint}", headers=headers)
        return response.json()

# Usage
client = MCPOAuthClient()
auth_url = client.get_authorization_url("client-id", "http://localhost:8080/callback")
print(f"Visit: {auth_url}")
# After authorization, exchange code for token
# token_data = client.exchange_code_for_token(code, "client-id", "http://localhost:8080/callback")
# result = client.call_protected_resource("/oauth/test")
```

This completes the OAuth 2.1 implementation for your MCP Docker Server with full MCP specification compliance!