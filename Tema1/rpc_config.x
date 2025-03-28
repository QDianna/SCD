struct AuthZRequest {
  string user_id<>;
};

struct AuthZResponse {
  string user_id<>;
  string token<>;
  int error_code;
  string message<>;
};

struct AccessTokenRequest {
  string user_id<>;
  string authz_token<>;
  int auto_refresh;
  string refresh_token<>;
};

struct AccessTokenResponse {
  string access_token<>;
  string refresh_token<>;
  int access_token_ttl;
  int error_code;
  string message<>;
};

struct DelegatedAction {
  string user_id<>;
  string operation<>;
  string resource<>;
  string access_token<>;
};

struct DelegatedActionResponse {
  int error_code;
  string message<>;
};


program OAUTH_PROG {
  version OAUTH_VERS {
    AuthZResponse requestAuthZ(AuthZRequest authz_request) = 1;
    AuthZResponse approveAuthZ(AuthZResponse authz_response) = 2;
    AccessTokenResponse generateAccessToken(AccessTokenRequest access_request) = 3;
    AccessTokenResponse refreshAccessToken(AccessTokenRequest access_request) = 4;
    DelegatedActionResponse executeDelegatedAction(DelegatedAction action) = 5;
  } = 1;
} = 0x20000001;


