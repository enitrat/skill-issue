# Narrative Tone & Writing Style

Rules for voice, tone, and prose style in SDK documentation.

## Voice

Use **second person ("you")** as the default voice. Switch to **first person plural ("we")** only during guided walkthroughs where you're building alongside the reader.

```
GOOD (general):  "You can configure the transport by passing options."
GOOD (tutorial): "First, we'll set up the config. Next, we'll wrap the app."
BAD:             "The transport is configured by passing options." (passive)
BAD:             "I recommend configuring the transport." (first person singular)
```

Use **imperative voice** for direct instructions:

```
GOOD: "Create a config.ts file and export a config object."
BAD:  "You should create a config.ts file."
```

### Voice by page type

| Page type | Primary voice | Example |
|-----------|--------------|---------|
| API reference | Second person | "Address to get balance for." |
| Getting started | Imperative + "you" | "Install the package. You can learn more..." |
| Step-by-step guide | "we" | "Next, we'll add the hook." |
| Why / Overview | Declarative | "Wagmi delivers a great developer experience." |
| Migration guide | Second person + imperative | "Update your imports. You no longer need..." |

## Tone

**Professional-casual with confidence.** Reads like a knowledgeable colleague explaining clearly — technically precise but not stiff.

### DO

- Make confident, declarative statements: "Performance is critical for applications of all sizes."
- Be direct and efficient: one clear sentence over three hedging ones
- Use parenthetical examples to ground concepts: `(e.g. fetching a block number, reading from a contract)`

### DON'T

- Use humor, slang, or exclamation marks (except sparingly in tutorial wrap-up steps like "Wire it up!")
- Hedge: "you might want to perhaps consider..." → "Use X when..."
- Be condescending: "Simply do X" or "Just add Y" (nothing is "simple" if you need docs for it)
- Use emoji (keep to near-zero usage; reserve only for celebrating TypeScript type inference wins)

## Sentence Structure

Target **10-25 words per sentence**. Never exceed 35 words without structural aids.

```
GOOD: "Performance is critical for applications of all sizes." (8 words)
GOOD: "Wagmi follows semver so developers can upgrade between versions with confidence." (11 words)
BAD:  "App developers should not need to worry about connecting tens of different wallets,
       the intricacies of multi-chain support, typos accidentally sending an order of
       magnitude more ETH..." (45 words without a break)
```

When longer sentences are necessary, use **colons, dashes, or parenthetical examples** as structural aids:

```
"Queries are used for fetching data (e.g. fetching a block number, reading from a contract),
and are typically invoked on mount by default."
```

## Concept Introduction

Follow the pattern: **brief framing → code → post-code commentary**.

1. One-sentence framing of what the reader will see
2. Code block
3. Optional 1-2 sentence commentary with link to deeper docs

```markdown
Create and export a new Wagmi config using `createConfig`.

[code block]

In this example, Wagmi is configured to use Mainnet and Sepolia. Check out the
`createConfig` docs for more configuration options.
```

Never write multiple paragraphs of explanation before showing code. If concept explanation exceeds 2 sentences, consider a dedicated "Why" or "Overview" page.

## Assumed Knowledge

### Assume the reader knows

- The host framework (React hooks, Vue composables, etc.)
- TypeScript basics (generics, type inference, const assertions)
- Domain fundamentals (for web3: wallets, transactions, contracts, ABIs, RPC)

### Always explain

- SDK-specific APIs and concepts
- Integration points with third-party libraries ("TanStack Query is an async state manager that handles requests, caching, and more.")
- Non-obvious behavior or gotchas

## Jargon Handling

| Pattern | Example |
|---------|---------|
| SDK term, first use | Explain inline: "Viem is a TypeScript interface for Ethereum" |
| Domain term, well-known | Use freely: ABI, RPC, hook, connector |
| Domain term, specific | Explain when relevant: "A read-only function (constant function) is denoted by a `pure` or `view` keyword" |

## Admonitions

| Type | Use for | Example |
|------|---------|---------|
| `::: warning` | "You must do this or things break" | "Make sure to replace the `projectId` with your own WalletConnect Project ID" |
| `::: info` | Reassurance or context | "Not ready to migrate yet? The v1 docs are still available at..." |
| `::: tip` | Helpful side-information | "TypeScript doesn't support importing JSON as const yet. Check out the CLI!" |
| `::: details` | Optional deeper dives | TypeScript configuration, advanced patterns |

## "Why" vs "How"

Documentation is weighted toward **"how"** (procedural instructions). "Why" appears in two places:

1. **Dedicated "Why" pages** — longer persuasive prose explaining project motivation
2. **Inline in migration guides** — when removing features, explain the benefit: "This is more code, but removes internal complexity from hooks and gives you more control."

API reference pages have **zero "why"**. They are pure reference.

## Transition Between Prose and Code

| Pattern | When to use |
|---------|-------------|
| Declarative sentence → code block | Most common. "Create and export a config." → [code] |
| Context-setting → code block | "Below, we render a list of connectors. When clicked, `connect` fires." → [code] |
| Code block → post-code commentary | After examples that need explanation. [code] → "In this example, we configured..." |
| "Check out the X docs" send-off | After every major section to link deeper |

## Parameter Descriptions

In API reference pages, parameter descriptions are **terse fragments**, not full sentences:

```
GOOD: "The contract's ABI."
GOOD: "Account to use when calling the contract (`msg.sender`)."
GOOD: "Block number to call contract at."
BAD:  "This parameter accepts the ABI of the contract that you want to interact with."
```
