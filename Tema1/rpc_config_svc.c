/*
 * Please do not edit this file.
 * It was generated using rpcgen.
 */

#include "rpc_config.h"
#include <stdio.h>
#include <stdlib.h>
#include <rpc/pmap_clnt.h>
#include <string.h>
#include <memory.h>
#include <sys/socket.h>
#include <netinet/in.h>

#ifndef SIG_PF
#define SIG_PF void(*)(int)
#endif

static void
oauth_prog_1(struct svc_req *rqstp, register SVCXPRT *transp)
{
	union {
		AuthZRequest requestauthz_1_arg;
		AuthZResponse approveauthz_1_arg;
		AccessTokenRequest generateaccesstoken_1_arg;
		AccessTokenRequest refreshaccesstoken_1_arg;
		DelegatedAction executedelegatedaction_1_arg;
	} argument;
	char *result;
	xdrproc_t _xdr_argument, _xdr_result;
	char *(*local)(char *, struct svc_req *);

	switch (rqstp->rq_proc) {
	case NULLPROC:
		(void) svc_sendreply (transp, (xdrproc_t) xdr_void, (char *)NULL);
		return;

	case requestAuthZ:
		_xdr_argument = (xdrproc_t) xdr_AuthZRequest;
		_xdr_result = (xdrproc_t) xdr_AuthZResponse;
		local = (char *(*)(char *, struct svc_req *)) requestauthz_1_svc;
		break;

	case approveAuthZ:
		_xdr_argument = (xdrproc_t) xdr_AuthZResponse;
		_xdr_result = (xdrproc_t) xdr_AuthZResponse;
		local = (char *(*)(char *, struct svc_req *)) approveauthz_1_svc;
		break;

	case generateAccessToken:
		_xdr_argument = (xdrproc_t) xdr_AccessTokenRequest;
		_xdr_result = (xdrproc_t) xdr_AccessTokenResponse;
		local = (char *(*)(char *, struct svc_req *)) generateaccesstoken_1_svc;
		break;

	case refreshAccessToken:
		_xdr_argument = (xdrproc_t) xdr_AccessTokenRequest;
		_xdr_result = (xdrproc_t) xdr_AccessTokenResponse;
		local = (char *(*)(char *, struct svc_req *)) refreshaccesstoken_1_svc;
		break;

	case executeDelegatedAction:
		_xdr_argument = (xdrproc_t) xdr_DelegatedAction;
		_xdr_result = (xdrproc_t) xdr_DelegatedActionResponse;
		local = (char *(*)(char *, struct svc_req *)) executedelegatedaction_1_svc;
		break;

	default:
		svcerr_noproc (transp);
		return;
	}
	memset ((char *)&argument, 0, sizeof (argument));
	if (!svc_getargs (transp, (xdrproc_t) _xdr_argument, (caddr_t) &argument)) {
		svcerr_decode (transp);
		return;
	}
	result = (*local)((char *)&argument, rqstp);
	if (result != NULL && !svc_sendreply(transp, (xdrproc_t) _xdr_result, result)) {
		svcerr_systemerr (transp);
	}
	if (!svc_freeargs (transp, (xdrproc_t) _xdr_argument, (caddr_t) &argument)) {
		fprintf (stderr, "%s", "unable to free arguments");
		exit (1);
	}
	return;
}

// reference to a method from 'rpc_config_server' that extracts input file names from the program's arguments
void get_arguments(int argc, char **argv);

int
main (int argc, char **argv)
{
	register SVCXPRT *transp;

	pmap_unset (OAUTH_PROG, OAUTH_VERS);

	transp = svcudp_create(RPC_ANYSOCK);
	if (transp == NULL) {
		fprintf (stderr, "%s", "cannot create udp service.");
		exit(1);
	}
	if (!svc_register(transp, OAUTH_PROG, OAUTH_VERS, oauth_prog_1, IPPROTO_UDP)) {
		fprintf (stderr, "%s", "unable to register (OAUTH_PROG, OAUTH_VERS, udp).");
		exit(1);
	}

	transp = svctcp_create(RPC_ANYSOCK, 0, 0);
	if (transp == NULL) {
		fprintf (stderr, "%s", "cannot create tcp service.");
		exit(1);
	}
	if (!svc_register(transp, OAUTH_PROG, OAUTH_VERS, oauth_prog_1, IPPROTO_TCP)) {
		fprintf (stderr, "%s", "unable to register (OAUTH_PROG, OAUTH_VERS, tcp).");
		exit(1);
	}

  // call method from 'rpc_config_server'
  get_arguments(argc, argv);

	svc_run ();
	fprintf (stderr, "%s", "svc_run returned");
	exit (1);
	/* NOTREACHED */
}
