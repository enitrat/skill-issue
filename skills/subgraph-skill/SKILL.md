---
name: zama-subgraph
description:
  "Best practices for building app-facing subgraphs and GraphQL integrations in this monorepo. Use
  when: (1) Setting up a new subgraph package, (2) Designing `schema.graphql` entities and
  relationships, (3) Choosing manifest strategy (`subgraph.yaml`, `networks.json`, or templating),
  (4) Writing AssemblyScript mappings and entity ID helpers, (5) Deciding when to use snapshots,
  immutable entities, templates, or helper entities, (6) Wiring app-side GraphQL queries against the
  subgraph, (7) Reviewing subgraph performance, maintainability, or testing strategy. Derived from
  studying production DeFi subgraphs and aligned to Zama's local stack."
---

# Subgraph Best Practices

## Core Model

### A Subgraph Has Two Jobs

1. Maintain a small set of **current-state entities** that the app can query cheaply.
2. Record **event/history entities** only when the product needs auditability, timelines, or
   activity feeds.

That framing should drive almost every design choice.

If a field is needed to render the current app state, keep it on a mutable entity. If a record
exists only because an event happened, make it an immutable event entity.

### Optimize For Query Shape, Not Indexing Cleverness

The best subgraph is not the one with the fanciest mapping layer. It is the one whose schema matches
the actual product queries.

Keep a current-state `Batch`, `Position`, `Vault`, `Market`, or equivalent entity. Add event/history
entities only where the UI or operators need them.

## Configuration Strategy

### Default: Static `subgraph.yaml` + `networks.json`

This should be the default for app-facing subgraphs.

Use it when:

- the same data sources exist on every network
- only addresses and start blocks vary
- you want simple builds like `graph build --network sepolia`

This is the right choice for a fixed-contract subgraph.

### Use Manifest Templating Only When Topology Changes

Use Mustache or similar templating when:

- some data sources only exist on some networks
- the manifest shape changes per deployment
- you need conditional handlers, grafting, or chain-specific manifest blocks

Do not introduce templating just because multiple networks exist. If `networks.json` is enough, use
it.

### Use Runtime Templates For Factory-Created Contracts

If contracts are created after indexing starts, use Graph templates.

```yaml
templates:
  - kind: ethereum/contract
    name: Vault
    network: mainnet
    source:
      abi: Vault
    mapping:
      kind: ethereum/events
      apiVersion: 0.0.7
      language: wasm/assemblyscript
      file: ./src/mappings.ts
      entities:
        - Vault
      abis:
        - name: Vault
          file: ./abis/Vault.json
      eventHandlers:
        - event: Deposit(indexed address,uint256)
          handler: handleDeposit
```

```typescript
import { Vault as VaultTemplate } from "../generated/templates";

export function handleVaultCreated(event: VaultCreated): void {
  VaultTemplate.create(event.params.vault);
}
```

## Schema Design

### Current-State Entities vs Event Entities

Use **mutable entities** for current state:

```graphql
type Batch @entity {
  id: ID!
  state: BatchState!
  exchangeRate: BigInt
  finalizedAtBlock: BigInt
  memberships: [PositionMembership!]! @derivedFrom(field: "batch")
}
```

Use **immutable entities** for event records:

```graphql
type BatchFinalizedEvent @entity(immutable: true) {
  id: Bytes!
  batch: Batch!
  exchangeRate: BigInt!
  blockNumber: BigInt!
  txHash: Bytes!
}
```

Rule:

- if the entity should change over time, it is mutable
- if the entity is a record of one event occurrence, it should usually be immutable

### `@derivedFrom` Is The Default For Reverse Relations

Do not store arrays of related entities directly when the relation can be expressed from the child
side.

```graphql
type Batch @entity {
  id: ID!
  memberships: [PositionMembership!]! @derivedFrom(field: "batch")
}

type PositionMembership @entity {
  id: ID!
  batch: Batch!
  account: Bytes!
}
```

Why:

- cleaner writes
- smaller mutable state surface
- better alignment with how Graph relationships are meant to be modeled

Important nuance:

- this applies to **entity relationship arrays**
- it does not mean "never use arrays anywhere"

Small scalar arrays can be fine. Relationship arrays should almost always be `@derivedFrom`.

### Snapshots Are A Product Feature

Add snapshots only when the app or analytics layer needs:

- time-series charts
- daily or hourly rollups
- point-in-time financial metrics
- unique-user or usage metrics by interval

Do not add snapshots just because other subgraphs have them.

For a simple app-facing state machine, snapshots are often unnecessary complexity.

If you need snapshots, make them deterministic:

```typescript
import { Bytes } from "@graphprotocol/graph-ts";

export function makeDailySnapshotId(entityId: Bytes, timestamp: i32): Bytes {
  return entityId.concat(Bytes.fromI32(timestamp / 86400));
}
```

## ID Strategy

### Use `Bytes!` When The Identity Is Naturally Binary

Use `Bytes!` for:

- addresses
- tx-hash + log-index event IDs
- binary composite IDs built from addresses and fixed-width values

```typescript
import { Bytes, ethereum } from "@graphprotocol/graph-ts";

export function makeEventId(event: ethereum.Event): Bytes {
  return event.transaction.hash.concatI32(event.logIndex.toI32());
}
```

This should be the default for event IDs.

### Use `ID!`/string When The Identity Is Semantic

Use string IDs when:

- the entity key is semantic rather than binary
- you need readable or versioned composites
- the identifier contains mixed domains like chain ID + address + protocol-side counter

```typescript
import { Address, BigInt } from "@graphprotocol/graph-ts";

export function makeBatchEntityId(chainId: i32, batcher: Address, batchId: BigInt): string {
  return `${chainId.toString()}-${batcher.toHexString()}-${batchId.toString()}`;
}
```

Do not force `Bytes!` everywhere. Use the ID shape that makes collisions impossible and the model
maintainable.

## Mapping Structure

### Default To Flat Helpers

For most app-facing subgraphs, flat helpers are the right starting point.

Typical layout:

```text
src/
├── mappings.ts
├── entity-ids.ts
└── helpers.ts
```

Use flat helpers when:

- handlers touch only a few entities
- the state machine is small
- there is little reuse across handlers

### Introduce Managers Only When The Domain Demands It

Manager classes are justified when handlers repeatedly update many entities with tightly coupled
logic.

The trigger is a single handler that updates current state, counters, snapshots, event entities, and
lifecycle/versioning helpers all at once. For a simple subgraph, managers are usually
over-architecture.

### Keep Handlers Thin

Handlers should do four things:

1. Decode event intent.
2. Load or create the required entities.
3. Update current state and write event entities.
4. Delegate repeated logic to helpers.

```typescript
export function handleJoined(event: Joined): void {
  const batch = getOrCreateBatch(event);
  const membership = getOrCreateMembership(event, batch);

  membership.status = "active";
  membership.joinedAtBlock = event.block.number;
  membership.save();

  batch.state = "pending";
  batch.save();
}
```

### Helper Entities Are Fine When They Buy Determinism

Use helper entities for things like:

- unique-account counting by interval
- lifecycle counters
- versioned position reopening

Do not add helper entities unless they remove ambiguity from the model.

## Performance And Manifest Knobs

### Pruning Is A Workload Decision

Use:

```yaml
indexerHints:
  prune: auto
```

when the subgraph is primarily app-facing and you care about current-state reads more than
historical entity versions.

Use:

```yaml
indexerHints:
  prune: never
```

when historical state retention matters.

Do not treat `prune: auto` as a universal best practice. It is a default for app-facing products,
not for every subgraph.

### Enable Receipts Only When Needed

```yaml
eventHandlers:
  - event: LiquidationCall(...)
    handler: handleLiquidationCall
    receipt: true
```

Do not enable `receipt: true` globally. It is a targeted feature.

### Prefer Event-Complete Contracts

The cleanest subgraph is one whose contracts emit the data the mappings need.

Contracts should emit enough data for the mapping to update state directly. Selective `eth_call` for
metadata or unavoidable derived state is acceptable.

## Testing

### Matchstick Is Required Here

The external repos are inconsistent. We should not copy that.

For this repo, Matchstick tests are part of the standard.

Test:

- ID construction
- lifecycle transitions
- edge cases
- duplicate-event behavior if relevant

```typescript
import { afterEach, assert, clearStore, test } from "matchstick-as/assembly/index";
import { handleDepositJoined } from "../src/mappings";
import { createJoinedEvent } from "./helpers";

afterEach(() => {
  clearStore();
});

test("handleDepositJoined creates a membership", () => {
  const event = createJoinedEvent();
  handleDepositJoined(event);

  assert.entityCount("PositionMembership", 1);
});
```

The point of these tests is not coverage theater. It is to lock down the parts of a subgraph that
are easy to silently break.

## Package Shape

Default package shape:

```text
packages/indexer/
├── abis/
├── src/
│   ├── mappings.ts
│   ├── entity-ids.ts
│   └── helpers.ts
├── tests/
│   └── helpers.ts
├── schema.graphql
├── subgraph.yaml
├── networks.json
└── package.json
```

Split further only when the domain complexity justifies it.

## Scripts

Default script shape:

```json
{
  "scripts": {
    "codegen": "graph codegen",
    "build": "pnpm run build:local",
    "build:local": "graph codegen && graph build --network local",
    "build:sepolia": "graph codegen && graph build --network sepolia",
    "build:mainnet": "graph codegen && graph build --network mainnet",
    "test": "graph test",
    "deploy:staging": "pnpm run build:sepolia && goldsky subgraph deploy <name>/staging --path .",
    "deploy:prod": "pnpm run build:mainnet && goldsky subgraph deploy <name>/prod --path ."
  }
}
```

If the manifest is templated, add an explicit generate/prepare step instead of pretending everything
fits the `--network` model.

## GraphQL Layer

See [references/graphql-layer.md](references/graphql-layer.md) for proxy implementation, client
setup, type safety escalation path, and schema validation test.

- For production apps, proxy subgraph queries through a server-side API route to hide keys and
  filter operations. For internal tools or local dev, direct queries are fine.
- Use `graphql-request` as a minimal transport. Pair with TanStack Query for caching, retries, and
  deduplication. Do not add retry logic at the GraphQL layer.
- Default to manual response types. Escalate to `gql.tada` when the query surface grows past ~10
  queries. Escalate to `@graphql-codegen` only for large surfaces with shared fragments.
- When not using codegen, validate query documents against `schema.graphql` in tests to catch drift.
- Keep queries small and purpose-built. Align response shapes to real app screens, not to the full
  schema.

## Local Development And Deploys

### Local Development

Prefer the repo's standard local flow around `gnd` when available.

Docker graph-node + IPFS + Postgres remains a valid fallback when:

- `gnd` is unavailable
- you need raw graph-node parity
- you are debugging infra-specific issues

### Deployment

Goldsky deployment is a deliberate operator action in this repo.

CI should:

- build
- test
- validate query documents

CI should not silently deploy unless that policy changes explicitly.

## Default Decision Path

When starting a new subgraph:

1. Model the product queries first.
2. Add current-state entities that make those queries cheap.
3. Add immutable event entities only where history is actually needed.
4. Use static manifest + `networks.json` unless the topology forces more.
5. Keep mappings flat until complexity clearly demands more structure.
6. Add snapshots only for real analytics needs.
7. Test IDs and lifecycle transitions before expanding scope.

## Anti-Patterns

| Anti-Pattern                                               | Why It Fails                                                              | Do This Instead                                                         |
| ---------------------------------------------------------- | ------------------------------------------------------------------------- | ----------------------------------------------------------------------- |
| Store raw events only, force frontend to reconstruct state | Subgraph queries can't replay state; every page load becomes expensive    | Keep current-state entities that the app queries directly               |
| Store entity-relationship arrays directly on parent        | Graph Node versions every array mutation — O(n) storage per update        | `@derivedFrom` for reverse relations                                    |
| Add snapshots because other subgraphs have them            | Each snapshot type adds thousands of entities/year and mapping complexity | Add snapshots only when a real analytics query needs them               |
| `@entity(immutable: true)` on entities that get updated    | Immutable entities silently ignore updates — data looks stale             | Only mark write-once event records as immutable                         |
| Force `Bytes!` IDs everywhere                              | Semantic composites become unreadable; debugging gets harder              | Use `Bytes!` for binary keys, `ID!` for semantic composites             |
| Introduce manager classes for a 5-entity subgraph          | Adds indirection without reducing complexity                              | Flat helpers until handlers routinely touch 5+ entities each            |
| `receipt: true` on all handlers                            | Fetches full receipt even when handler doesn't read it                    | Enable only on handlers that need gas or receipt data                   |
| `prune: auto` as a universal default                       | Destroys historical entity versions needed for analytics or auditing      | Choose pruning explicitly based on workload                             |
| `eth_call` in every high-frequency handler                 | Each call adds 100ms+ indexing latency                                    | Emit needed data as contract events; call only for one-time metadata    |
| Manifest templating for a fixed-topology subgraph          | Adds a build step and generated files for no benefit                      | Use `networks.json` when only addresses/startBlocks vary                |
| Query the subgraph directly from the browser in prod       | Exposes API keys and subgraph URL; no request validation                  | Proxy through a server-side API route                                   |
| Add `@graphql-codegen` pipeline for 3 queries              | Build step overhead exceeds the type safety benefit                       | Manual types for small surfaces; `gql.tada` as a lightweight escalation |
