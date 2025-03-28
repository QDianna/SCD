/*
 * This is sample code generated by rpcgen.
 * These are only templates and you can use them
 * as a guideline for developing your own functions.
 * 
 * This server implements both the AuthZ Server and the Resource Server
 * as described in the OAuth architecture.
 * 
 * Responsibilities:
 * 1. AuthZ Server:
 *    - Handles AuthZ requests (requestAuthZ) from the client, validating the user and generating an AuthZ token.
 *    - Simulates end-user approval (approveAuthZ) based on data from the approvals.db file.
 *    - Manages Access Tokens (generateAccessToken) and Refresh Tokens.
 * 
 * 2. Resource Server:
 *    - Validates and processes Delegated Actions (executeDelegatedAction) on resources loaded from resources.db.
 * 
 * Simulated End-User:
 * - The end-user is simulated via the 'approveAuthZ' function, which reads approval/responses from approvals.db.
 * - Approvals are handled in FIFO order.
 * 
 * Files required by this server:
 * - users.db: A list of valid user IDs.
 * - approvals.db: Simulated responses for end-user approvals.
 * - resources.db: A list of resources and permissions available on the server.
 */

#include "rpc_config.h"
#include "token.h"
#include <stdio.h>
#include <string.h>
#include <stdlib.h>

#define MAX_REQUESTS 100
#define LINE_SIZE 256
#define USER_ID_LENGTH 15

// files used by server
static char* userIDs_file;
static char* resources_file;
static char* approvals_file;

// structure used for managing permissions of each user
typedef struct {
  int count;
  char* resource;
  char* permitted_ops;
} Permissions;

// structure used for managing user's valid authorization and access tokens
// and the permissions associated with them
typedef struct {
  char* user_id;
  char* authz_token;
  char* access_token;
  char* refresh_token;
  int ttl;
  Permissions* permissions;
} ValidTokens;


static ValidTokens valid_tokens[MAX_REQUESTS];
static int valid_tokens_index = 0;
static char approvals[MAX_REQUESTS][LINE_SIZE];
static int current_approval_index = 0;
static int token_ttl = 0;
static char* indent = "  ";


/**
 * This function is called by the stub at the start.
 * Gets server's input files and token ttl from program arguments and clears the output file.
*/
void get_arguments(int argc, char **argv) {
    if (argc < 5) {
        fprintf(stderr, "Usage: %s <userIDs_file> <resources_file> <approvals_file> <token_ttl>\n", argv[0]);
        exit(1);
    }

    userIDs_file = argv[1];
    resources_file = argv[2];
    approvals_file = argv[3];

    token_ttl = atoi(argv[4]);
    if (token_ttl < 0) {
        fprintf(stderr, "Invalid TTL value. Must be a positive integer: %s.\n", argv[4]);
        exit(1);
    }

    FILE *server_output = fopen("server.out", "w");
    if (server_output == NULL) {
        perror("Error opening output file for clearing");
        exit(1);
    }
    fclose(server_output);
}


/**
 * Checks if the user given as parameter exists in the 'userIDs.db' file.
 */
int find_user(char* user_id, const char* users_file) {
  FILE *file = fopen(users_file, "r");
  if (file == NULL) {
    perror("userIDs file not found\n");
    return -1;
  } 

  char line[LINE_SIZE];
  int users_count = 0;

  if (fgets(line, LINE_SIZE, file)) {
    users_count = atoi(line);

    for (int i = 1; i <= users_count; i ++) {
      if (!fgets(line, LINE_SIZE, file)) {
        fclose(file);
        return 0;
      }

      line[strcspn(line, "\n")] = '\0';

      if (!strcmp(user_id, line)) {
        fclose(file);
        return 1;
      }
    }
  }

  fclose(file);
  return 0;
}


/**
 * Reads the 'approvals.db' file and stores each line in the 'approvals' array.
 */
void read_approvals(const char* approvals_file) {
  FILE *file = fopen(approvals_file, "r");
  if (file == NULL) {
    perror("approvals file not found");
    exit(1);
  } 

  char current_approval[LINE_SIZE];
  int index = 0;

  while (fgets(current_approval, LINE_SIZE, file)) {
    current_approval[strcspn(current_approval, "\n")] = '\0';
    strcpy(approvals[index], current_approval);
    index ++;
  }

  fclose(file);
}


/**
 * Checks if the resource given as parameter exists in the 'resources.db' file.
 */
int find_resource(const char* resources_file, const char* resource) {
  FILE *file = fopen(resources_file, "r");
  if (file == NULL) {
    perror("Resources file not found");
    return -1;
  }

  char current_resource[LINE_SIZE];

  while (fgets(current_resource, LINE_SIZE, file)) {
    current_resource[strcspn(current_resource, "\n")] = '\0';
    if (!strcmp(resource, current_resource))
      return 1;
  }

  fclose(file);
  return 0;
}


/**
 * This function gets a line/an "approval" from the 'approvals.db' file and parses it, determining
 * each resource and the permissions associated with it.
 * It writes directly into the 'permissions' field of the 'valid_tokens' structure
 * for the user that recieved this specific approval.
 */
void parse_permissions(const char* approval, Permissions** permissions_out) {
    char* approval_copy = strdup(approval);
    char* token = strtok(approval_copy, ",");

    int count = 0;
    Permissions* permissions = malloc(LINE_SIZE * sizeof(Permissions));

    while (token != NULL) {
        permissions[count].resource = strdup(token);
        
        token = strtok(NULL, ",");
        if (token == NULL) 
          break;

        permissions[count].permitted_ops = strdup(token);

        token = strtok(NULL, ",");
        count++;
    }

    permissions->count = count;
    *permissions_out = permissions;
}


/**
 * This function approves/denies an operation that a user is trying to do.
 * It checks if the operation and the resource (both given as parameters)
 * exist in the 'permissions' data structure of the server for this user.
 */
int validate_operation(int index, const char* operation, const char* resource) {
    if (!find_resource(resources_file, resource))
      return 2;  // resource not found

    Permissions* permissions = valid_tokens[index].permissions;

    char *op = (strcmp(operation, "READ") == 0) ? "R" :
               (strcmp(operation, "INSERT") == 0) ? "I" :
               (strcmp(operation, "MODIFY") == 0) ? "M" :
               (strcmp(operation, "DELETE") == 0) ? "D" :
               (strcmp(operation, "EXECUTE") == 0) ? "X" : "UNKOWN_OP";

    for (int i = 0; i < permissions->count; i ++) {
        if (!strcmp(permissions[i].resource, resource)) {
            if (strstr(permissions[i].permitted_ops, op)) {
                return 0; // permission granted
            } else {
              return 1; // operation not permitted
            }
        }
    }

    return 1; // operation not permitted
}


/**
 * This method is called by the client to request an authz token.
 * The server checks if the request is valid and generates an authz token if so.
 * If the request is not valid, the server returns an empty token with an error code
 * and meesage specifying the problem.
*/
AuthZResponse *
requestauthz_1_svc(AuthZRequest *argp, struct svc_req *rqstp)
{
	static AuthZResponse  result;
  char* u_id = argp->user_id;

  // reset the static result structure
  memset(&result, 0, sizeof(AuthZResponse));

  FILE *server_output = fopen("server.out", "a");
  if (server_output == NULL) {
    perror("Couldnt open server output file");
    exit(1);
  }

  fprintf(server_output, "BEGIN %s AUTHZ\n", u_id);
  
  // check for a valid user id
  if (u_id == NULL || strlen(u_id) != USER_ID_LENGTH) {
    result.user_id = u_id;
    result.token = "";
    result.error_code = 1;
    result.message = "INVALID_USER_ID";
    fclose(server_output);
	  return &result;
  }

  // check for known user
  if (find_user(u_id, userIDs_file) != 1) {
    result.user_id = u_id;
    result.token = "";
    result.error_code = 2;
    result.message = "USER_NOT_FOUND";
    fclose(server_output);
	  return &result;
  }

  result.user_id = strdup(u_id);
  result.token = generate_access_token(u_id);
  result.error_code = 0;
  result.message = "AUTHZ_REQUEST_GRANTED";

  fprintf(server_output, "%sRequestToken = %s\n", indent, result.token);
  fclose(server_output);
	return &result;
}


/**
 * This method is called by the client to validate the autz token and get a permission token.
 * The server simulates an end-user through the 'approvals.db' file that "gives responses" to the
 * access request. The end-user either grants certain permissions or denies access.
 * If the token is authorized, the server stores the permissions associated with the user and token.
 */
AuthZResponse *
approveauthz_1_svc(AuthZResponse *argp, struct svc_req *rqstp)
{
	static AuthZResponse  result;

  // reset the static result structure
  memset(&result, 0, sizeof(AuthZResponse));

  if (!current_approval_index) {
    // first time using approvals so must read them first
    read_approvals(approvals_file);
  }

  char *approval = approvals[current_approval_index];
  current_approval_index ++;

  if (approval == NULL || strlen(approval) == 0) {
    result.user_id = strdup(argp->user_id);
    result.token = "";
    result.error_code = -1;
    result.message = "APPROVAL_NOT_FOUND";
    return &result;
  }

  if (!strcmp(approval, "*,-")) {
    result.user_id = strdup(argp->user_id);
    result.token = "";
    result.error_code = -2;
    result.message = "REQUEST_DENIED";
    return &result;
  }

  result.user_id = strdup(argp->user_id);
  result.token = strdup(argp->token);
  result.error_code = 0;
  result.message = "AUTHZ_VALIDATION_DONE";
	
  for (int i = 0; i < valid_tokens_index; i ++) {
    if (!strcmp(valid_tokens[i].user_id, argp->user_id)) {
      // refresh info from server's data-structure 'valid_tokens' if user already exists
      valid_tokens[i].authz_token = strdup(argp->token);
      parse_permissions(approval, &valid_tokens[i].permissions);
      valid_tokens[i].access_token = "";
      valid_tokens[i].refresh_token = "";
      valid_tokens[i].ttl = 0;
      return &result;
    }
  }
  // create new entry in server's data-structure if user doesnt exist
  valid_tokens[valid_tokens_index].user_id = strdup(argp->user_id);
  valid_tokens[valid_tokens_index].authz_token = strdup(argp->token);
  parse_permissions(approval, &valid_tokens[valid_tokens_index].permissions);
  valid_tokens[valid_tokens_index].access_token = "";
  valid_tokens[valid_tokens_index].refresh_token = "";
  valid_tokens[valid_tokens_index].ttl = 0;
  valid_tokens_index ++;

	return &result;
}


/**
 * This method is called by the client to request an access token using an authz token.
 * The server checks if the request is valid and either generates an acces token
 * (and a refresh token if the request specifies) or returns an empty token and an
 * error code & message.
 */
AccessTokenResponse *
generateaccesstoken_1_svc(AccessTokenRequest *argp, struct svc_req *rqstp)
{
	static AccessTokenResponse result;

	// reset the static result structure
  memset(&result, 0, sizeof(AccessTokenResponse));

  // check if the authz token used is valid and belongs to this user
  for (int i = 0; i < valid_tokens_index; i ++) {
    if (!strcmp(argp->user_id, valid_tokens[i].user_id) && !strcmp(argp->authz_token, valid_tokens[i].authz_token)) {
      char* access_token = generate_access_token(argp->authz_token);
      char* refresh_token;

      if (argp->auto_refresh) {
        refresh_token = generate_access_token(access_token);
        valid_tokens[i].refresh_token = strdup(refresh_token);
        result.refresh_token = strdup(refresh_token);
      } else {
         valid_tokens[i].refresh_token = "";
         result.refresh_token = "";
      }

      // save valid tokens in the server data structure for future checks
      valid_tokens[i].access_token = strdup(access_token);
      valid_tokens[i].ttl = token_ttl;

      result.access_token = strdup(access_token);
      result.access_token_ttl = token_ttl;
      result.error_code = 0;
      result.message = "ACCESS_REQUEST_GRANTED";

      FILE *server_output = fopen("server.out", "a");
      if (server_output == NULL) {
        perror("Couldnt open server output file");
        exit(1);
      }

      fprintf(server_output, "%sAccessToken = %s\n", indent, access_token);
      if (argp->auto_refresh)
        fprintf(server_output, "%sRefreshToken = %s\n", indent, refresh_token);

      fclose(server_output);

      return &result;
    }
  }

  result.access_token = "";
  result.refresh_token = "";
  result.access_token_ttl = 0;
  result.error_code = -1;
  result.message = "PERMISSION_DENIED";
  return &result;
}


/**
 * This method is called by the client to request an access token when his/hers previous token is about to expire
 * and he/she has auto refresh enabled.
 * Same method as the one above, but the client uses the refresh token instead of an authz token
 * to get an access token.
 */
AccessTokenResponse *
refreshaccesstoken_1_svc(AccessTokenRequest *argp, struct svc_req *rqstp)
{
	static AccessTokenResponse  result;

	// reset the static result structure
  memset(&result, 0, sizeof(AccessTokenResponse));

  FILE *server_output = fopen("server.out", "a");
  if (server_output == NULL) {
    perror("Couldnt open server output file");
    exit(1);
  }

  fprintf(server_output, "BEGIN %s AUTHZ REFRESH\n", argp->user_id);
  
  // check if the refresh token used is valid and belongs to this user
  for (int i = 0; i < valid_tokens_index; i ++) {
    if (!strcmp(argp->user_id, valid_tokens[i].user_id) && !strcmp(argp->refresh_token, valid_tokens[i].refresh_token)) {
      char* refreshed_access_token = generate_access_token(argp->refresh_token);
      char* refreshed_refresh_token = generate_access_token(refreshed_access_token);
      
      valid_tokens[i].access_token = strdup(refreshed_access_token);
      valid_tokens[i].refresh_token = strdup(refreshed_refresh_token);
      valid_tokens[i].ttl = token_ttl;

      result.access_token = strdup(refreshed_access_token);
      result.refresh_token = strdup(refreshed_refresh_token);
      result.access_token_ttl = token_ttl;
      result.error_code = 0;
      result.message = "ACCESS_REFRESHED";

      fprintf(server_output, "%sAccessToken = %s\n", indent, result.access_token);
      fprintf(server_output, "%sRefreshToken = %s\n", indent, result.refresh_token);

      fclose(server_output);
      return &result;
    }
  }

  result.access_token = "";
  result.refresh_token = "";
  result.access_token_ttl = 0;
  result.error_code = -1;
  result.message = "PERMISSION_DENIED";
  
  fclose(server_output);
  return &result;
}

/**
 * This method is called by the client to execute an action on a resource from the resource server.
 * The server checks if the action is permitted according to the access token used (and the permissions
 * associated) and the user that used it.
 * The server either executed/denies the client's action.
 */
DelegatedActionResponse *
executedelegatedaction_1_svc(DelegatedAction *argp, struct svc_req *rqstp)
{
	static DelegatedActionResponse  result;

  // reset the static result structure
	memset(&result, 0, sizeof(DelegatedActionResponse));

  FILE *server_output = fopen("server.out", "a");
  if (server_output == NULL) {
    perror("Couldnt open server output file");
    exit(1);
  }

  // check for access token
  if (!argp->access_token || strlen(argp->access_token) == 0) {
    result.error_code = 3;
    result.message = "PERMISSION_DENIED";
    fprintf(server_output, "DENY (%s,%s,%s,%d)\n", argp->operation, argp->resource, "", 0);
    fclose(server_output);
    return &result;
  }

  // check if access token is valid and belongs to the user that used it
  for (int i = 0; i < valid_tokens_index; i ++) {
    if (!strcmp(argp->user_id, valid_tokens[i].user_id) && !strcmp(argp->access_token, valid_tokens[i].access_token)) {
      if (valid_tokens[i].ttl) {
        valid_tokens[i].ttl --;
      }
      else {
        result.error_code = -1;
        result.message = "TOKEN_EXPIRED";

        // remove the invalid token from the server's data structure
        valid_tokens[i].access_token = "";
        
        fprintf(server_output, "DENY (%s,%s,%s,%d)\n", argp->operation, argp->resource, valid_tokens[i].access_token, valid_tokens[i].ttl);
        fclose(server_output);
        return &result;
      }
      
      // check if operation is permitted for this user on this resource
      int check = validate_operation(i, argp->operation, argp->resource);
      if (check == 0) {
        result.error_code = 0;
        result.message = "PERMISSION_GRANTED";
        fprintf(server_output, "PERMIT (%s,%s,%s,%d)\n", argp->operation, argp->resource, valid_tokens[i].access_token, valid_tokens[i].ttl);
        fclose(server_output);
        return &result;
      } 
      
      else if (check == 1) {
        result.error_code = 1;
        result.message = "OPERATION_NOT_PERMITTED";
        fprintf(server_output, "DENY (%s,%s,%s,%d)\n", argp->operation, argp->resource, valid_tokens[i].access_token, valid_tokens[i].ttl);
        fclose(server_output);
        return &result;
      } 
      
      else if (check == 2) {
        result.error_code = 2;
        result.message = "RESOURCE_NOT_FOUND";
        fprintf(server_output, "DENY (%s,%s,%s,%d)\n", argp->operation, argp->resource, valid_tokens[i].access_token, valid_tokens[i].ttl);
        fclose(server_output);
        return &result;
      }
    } 
  }

  result.error_code = 3;
  result.message = "PERMISSION_DENIED";
	return &result;
}

