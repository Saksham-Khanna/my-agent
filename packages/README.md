# packages/

Reserved for code shared between `apps/desktop` and `apps/api` (for
example, a generated TypeScript client for the event protocol, or shared
JSON-schema definitions).

**Phase 0 status: intentionally empty.**

Per `docs/ENGINEERING_RULES.md` ("avoid speculative abstractions"), this
repository does not create a shared package until a real duplication
problem exists. Right now the desktop app's types
(`apps/desktop/src/state/types.ts`, `apps/desktop/src/state/orbState.ts`)
and the API's Pydantic models (`apps/api/app/core/config.py`) are small
enough to stay independent.

Revisit this once `docs/EVENT_PROTOCOL.md` payloads need to be type-safe
on both sides (planned no earlier than Phase 2).
