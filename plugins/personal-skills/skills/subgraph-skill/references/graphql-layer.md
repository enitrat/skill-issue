# GraphQL Client Layer

Recommended architecture for wiring an app to a subgraph.

## Architecture

### Proxy the subgraph behind an API route

For production apps, route subgraph queries through a server-side endpoint rather than exposing the
subgraph URL to the browser. This hides API keys, lets you reject unwanted operations, and decouples
the frontend from the subgraph deployment URL.

For internal tools, dashboards, or development, querying the subgraph directly is fine.

### Lightweight request validation

The proxy should apply basic guardrails:

1. **Operation filtering** — parse the document and reject mutations/subscriptions. Subgraphs are
   read-only; the proxy should enforce that.
2. **Introspection control** — block `__schema`/`__type` in production if you don't want the schema
   publicly discoverable.
3. **Body size cap** — reject oversized payloads before parsing (16-64KB is reasonable).

```typescript
// api/graphql/route.ts
import { parse } from "graphql";

const MAX_BODY = 16 * 1024;
const INTROSPECTION_ALLOWED = process.env.NODE_ENV !== "production";

function jsonError(msg: string, status: number) {
  return Response.json({ error: msg }, { status });
}

function isQueryOnly(source: string): boolean {
  return parse(source).definitions.every(
    (d) => d.kind !== "OperationDefinition" || d.operation === "query",
  );
}

function containsIntrospection(query: string): boolean {
  return /(^|[^A-Za-z0-9_])__(schema|type)\b/.test(query);
}

export async function POST(req: Request) {
  const url = process.env.SUBGRAPH_URL;
  if (!url) return jsonError("SUBGRAPH_URL not set", 500);

  const body = await req.text();
  if (body.length > MAX_BODY) return jsonError("Too large", 413);

  let payload: { query?: string };
  try {
    payload = JSON.parse(body);
  } catch {
    return jsonError("Bad JSON", 400);
  }
  if (!payload.query) return jsonError("Missing query", 400);

  try {
    if (!isQueryOnly(payload.query)) return jsonError("Queries only", 403);
  } catch {
    return jsonError("Invalid GraphQL", 400);
  }

  if (!INTROSPECTION_ALLOWED && containsIntrospection(payload.query))
    return jsonError("Introspection disabled", 403);

  const headers: Record<string, string> = { "Content-Type": "application/json" };
  if (process.env.SUBGRAPH_KEY) headers["Authorization"] = `Bearer ${process.env.SUBGRAPH_KEY}`;

  try {
    const res = await fetch(url, { method: "POST", headers, body, cache: "no-store" });
    if (!res.ok) return jsonError("Upstream error", 502);
    return new Response(res.body, {
      status: res.status,
      headers: { "Content-Type": "application/json" },
    });
  } catch {
    return jsonError("Upstream error", 502);
  }
}
```

## Client Setup

Use `graphql-request` as a minimal transport layer. Point it at the proxy endpoint.

```typescript
import { GraphQLClient } from "graphql-request";

// Adjust the base URL to match your deployment. The proxy path is the only constant.
export const subgraphClient = new GraphQLClient("/api/graphql");
```

If server-side rendering or non-browser contexts need an absolute URL, resolve the host from your
deployment platform's conventions. Do not bake environment-variable resolution into the client
constructor — handle it at the call site or in middleware.

## Caching and Retries

Use TanStack Query (or your app's existing query cache) for caching, deduplication, and retries. Do
not add retry logic at the GraphQL transport layer.

```typescript
import { useQuery } from "@tanstack/react-query";
import { subgraphClient } from "@/lib/graphql";

export function usePositions(account: string) {
  return useQuery({
    queryKey: ["positions", account],
    queryFn: () => subgraphClient.request<PositionsResult>(POSITIONS_QUERY, { account }),
    enabled: Boolean(account),
  });
}
```

## Type Safety

### Default: manual types

For a small number of queries, define response types alongside the query strings. Simple, no tooling
required.

```typescript
const BATCH_QUERY = /* GraphQL */ `
  query Batch($id: ID!) {
    batch(id: $id) {
      id
      state
      totalDeposits
      memberCount
    }
  }
`;

type BatchResult = {
  batch: { id: string; state: string; totalDeposits: string; memberCount: number } | null;
};
```

### Escalation: `gql.tada`

When the query surface grows past ~10 queries or you start seeing type drift, switch to `gql.tada`.
It infers types at compile time from schema introspection — no build step, no codegen pipeline.

### Escalation: `@graphql-codegen`

For large query surfaces with shared fragments across many components, use `@graphql-codegen` with
the `client` preset. This is the heaviest option and adds a build step. Only worth it when the query
surface justifies it.

## Schema Validation Test

When not using codegen, validate that query documents parse against the subgraph schema at test
time. This catches field renames, removed types, and argument mismatches before they reach
production.

```typescript
import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import { buildSchema, parse, validate } from "graphql";
import { describe, expect, it } from "vitest";

// Declare Graph Protocol scalars and directives so buildSchema accepts the subgraph schema.
// Declare a root Query type mirroring graph-node's auto-generated query fields for
// each entity you actually query.
const GRAPH_PREAMBLE = `
  scalar BigInt
  scalar Bytes
  directive @entity(immutable: Boolean) on OBJECT
  directive @derivedFrom(field: String!) on FIELD_DEFINITION
  type Query {
    batch(id: ID!): Batch
    positionMemberships(where: PositionMembership_filter): [PositionMembership!]!
  }
  input PositionMembership_filter { account: Bytes; status_in: [MembershipStatus!] }
`;

// Point at the subgraph package's schema.graphql — adjust the path to match your monorepo layout.
const SCHEMA_PATH = resolve(__dirname, "../../subgraph/schema.graphql");

const schema = buildSchema(`${GRAPH_PREAMBLE}\n${readFileSync(SCHEMA_PATH, "utf8")}`);

describe("subgraph query documents", () => {
  it("batch query validates", () => {
    expect(validate(schema, parse(BATCH_QUERY))).toEqual([]);
  });
  // One test per query document.
});
```

The `GRAPH_PREAMBLE` must include: scalars (`BigInt`, `Bytes`), directives (`@entity`,
`@derivedFrom`), a `Query` root type with entries for each entity you query, and any `_filter` input
types used in `where` clauses. Update it as the schema evolves.

When you adopt codegen, this test becomes redundant — codegen validates against the schema as part
of its build step.
