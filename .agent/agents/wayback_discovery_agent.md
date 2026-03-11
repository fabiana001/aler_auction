name: wayback_discovery_agent
description: Discover and filter historical Wayback Machine snapshots.
model: gpt-4.1
instructions: |
  1. Use `WaybackClient` to query the CDX API for snapshots of `alermipianovendite.it/asta-alloggi/`.
  2. Filter discovered snapshots to identify those likely to contain auction announcements.
  3. Output a list of valid Wayback URLs for the extraction phase.
memory: project
tools:
  - wayback_client
