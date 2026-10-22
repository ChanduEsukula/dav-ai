# Dav AI — Revocation Trust Design

Status: PROPOSED — NOT IMPLEMENTED

## Trust boundaries

The pharmaceutical application must not control the private
signing keys used to issue or revoke deployment approvals.

Trusted public keys must be provisioned through an independently
controlled, authenticated configuration mechanism.

## Signed revocation records

A revocation record should contain:

- schema_version
- authority_id
- key_id
- sequence_number
- issued_at
- expires_at
- revoked_approval_ids
- revoked_signing_key_ids

The entire canonical record must be signed using an approved
asymmetric signature algorithm.

## Replay protection

Reject signatures from unknown or revoked authorities.

Reject sequence numbers lower than the highest previously
accepted sequence for the same authority.

A trusted monotonic high-water mark must survive application
restarts, container replacement, and deployment rollback.

## Availability

Revocation information must remain current.

Missing, invalid, stale, or unverifiable state fails closed.

The exact refresh cadence and maximum staleness require
independent approval before private staging is enabled.

## Key rotation

Support overlapping trusted keys during controlled rotation.

Revoked signing keys must stop authorizing approvals.

Emergency key revocation must have a documented response path.

## Production restrictions

Public production remains denied.

A staging approval cannot authorize public production.

## Implementation status

No authenticated revocation distribution, persistent anti-rollback
store, or production signing authority has been implemented.

The current offline revocation checker is test-only.

Do not connect it to the pharmaceutical serving gate yet.
