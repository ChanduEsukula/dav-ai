# Dav AI — Private Staging Authorization Design

Status: PROPOSED — NOT IMPLEMENTED

## Objective

Allow the exact approved pharmaceutical release to be served
only within independently authenticated private staging.

Public production remains denied.

## Required security boundaries

1. Authenticated TLS ingress protects all frontend and API paths.
2. No direct backend or frontend-origin bypass is permitted.
3. Staging uses explicit DAVAI_ENV=staging.
4. The pharmaceutical artifact is mounted read-only.
5. Serving requires a valid, independently signed authorization.
6. Authorization is bound to the exact release ID, SHA256,
   deployment identity, environment and private audience.
7. Missing, expired, revoked, malformed or mismatched
   authorization fails closed.
8. Authorization is checked at startup, readiness and data access.
9. Public production does not accept private staging authorization.
10. Artifact installation and activation never grant serving rights.

## Authorization document

Proposed fields:

- approval_id
- key_id
- release_id
- database_sha256
- environment
- audience
- deployment_id
- issued_at
- expires_at

Use a reviewed asymmetric signature format with canonical
serialization and explicit algorithm restrictions.

The private signing key must not be stored in the application,
repository, container image or artifact installation store.

## Revocation

A trusted revocation mechanism must reject revoked approvals
without requiring an application restart.

Define its availability, refresh, maximum staleness, failure
behavior and emergency revocation procedures before implementation.

## Deployment constraints

The current Docker staging configuration is a non-serving
blueprint.

Do not deploy it until independently authenticated ingress
and release-bound private authorization are implemented,
tested and approved.

## Acceptance criteria

- Unauthorized users cannot reach staging content or APIs.
- Direct-origin bypass attempts fail.
- Forged or modified approval documents fail.
- Wrong artifact, environment or deployment identity fails.
- Expired and revoked approvals deny readiness and data access.
- Production remains denied.
- Existing local pharmaceutical tests continue passing.
- Frozen database and publication metadata remain unchanged.

## Open decisions

- Private ingress provider and identity system
- Approval signing authority and key rotation
- Revocation authority and maximum staleness
- Deployment identity attestation
- Target persistent storage and operator ownership
- Independent reviewer and acceptance process
