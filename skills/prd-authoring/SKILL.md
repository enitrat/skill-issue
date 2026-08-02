---
name: prd-authoring
description: Guide for writing and reviewing clear, persuasive Product Requirements Documents (PRDs), including product proposals, feature proposals, and PRD feedback.

---

# Authoring Guide for Product Requirements Documents (PRDs)

A guide to writing clear, persuasive PRDs that align stakeholders, communicate user value, and enable implementation. This guide focuses on the craft of writing—how to structure arguments, explain proposals, and communicate product changes effectively.

---

## Philosophy

### PRDs Are Arguments for User Value, Not Technical Specs

A PRD is not a technical specification or design document. It is an argument for why users need this change and why this approach delivers value. Every section builds toward that argument: the problem establishes that user pain is real, the goals show what success looks like, the solution shows your approach addresses the problem, and the metrics prove we can measure impact.

If reviewers finish reading and don't understand why this matters to users or the business, the PRD has failed—regardless of how well-researched the solution is.

**Key principle**: PRDs define the **what** and **why**. Design docs and RFCs define the **how**.

### Write for Multiple Audiences

Your reviewers include product managers, engineers, designers, business stakeholders, and leadership. They skim looking for relevance (Summary), user problems (Motivation), business value (Goals, Metrics), what we're building (Solution, Requirements), and what could go wrong (Risks). Structure your PRD so each audience finds what matters to them quickly. Front-load the important information—don't bury context in paragraph four.

### PRDs Are Living Documents

PRDs used to be lengthy, rigid documents signed off once. Today they are leaner, iterative, and collaborative. Start with a draft to gather feedback early, update as you validate assumptions, and refine as implementation reveals new constraints. Keep it concise: 2-10 pages, clarity over length. When you find yourself answering the same question multiple times in comments, the PRD itself needs clarification.

---

## The Narrative Approach

### Tell a Story, Don't List Facts

The best PRDs read as a coherent narrative, not a collection of disconnected sections. Use the **ABT (And-But-Therefore)** method:

```
"Here's what users can do today..." (AND - Context)
    ↓
"But they face this problem..." (BUT - Problem/Gap)
    ↓
"Therefore, we propose this solution..." (THEREFORE - Resolution)
    ↓
"Here's how we measure success..." (Impact)
```

This narrative structure helps reviewers follow your reasoning and arrive at the same conclusion you did.

### Use Prose, Not Just Bullet Points

Bullet points work for discrete lists of items. They fail at explaining reasoning or building arguments. Compare:

```markdown
❌ Bullet-point thinking:

- Users can't track yield across protocols
- Manual tracking is error-prone
- Need aggregated dashboard
- Build pooling interface

✅ Narrative explanation:

Individual DeFi users currently track their positions across 5-8 different protocols
manually, copying balances into spreadsheets. This manual process leads to errors in
~30% of cases (user research, n=50) and takes 15-20 minutes daily. By providing an
aggregated dashboard that automatically pulls position data from connected wallets, we
reduce tracking time to under 1 minute and eliminate calculation errors entirely.
```

The narrative version explains **why** each piece matters and **how** they connect. Reviewers understand not just what you're proposing, but why it makes sense.

### Front-Load Context

Don't make readers wait for essential context. The first paragraph of each section should orient the reader:

```markdown
❌ Context buried:

The new feature will show APY history over 30 days with sparklines. Users can toggle
between protocols. This solves the comparison problem we identified in Q3 research.

✅ Context first:

Today, users cannot compare yield rates across protocols without manually tracking daily
APYs. User research (Q3 2025, n=120) found that 78% of active DeFi users want historical
APY comparison to inform their decisions. This PRD proposes an APY comparison dashboard
showing 30-day trends across connected protocols.
```

### Information Retention Through Storytelling

Research shows information presented in storytelling format is **20 times more likely to be retained** than facts presented linearly. Structure your PRD to create a clear problem → solution → impact arc, use concrete examples and user scenarios, and show before/after comparisons with specific metrics.

---

## Section-by-Section Guide

### Summary

**Purpose:** Let readers decide in 30 seconds if this PRD is relevant to them.

**Length:** 3-4 sentences maximum. Include the problem (user pain), what we're building (the solution), and what value it delivers. Leave implementation details for the design doc, background context for Motivation, and justifications for later sections.

```markdown
❌ Too long, too detailed:

This PRD proposes building a DeFi pooling aggregator that allows users to deposit funds
into a smart contract which then allocates across multiple yield protocols based on APY
optimization algorithms. Currently, users face high gas fees when interacting with
individual protocols, and they lack the sophistication to optimize yield strategies. Our
solution will reduce gas costs by 60% through batched transactions and increase average
yields by 2-4% through algorithmic optimization.

✅ Concise and clear:

Enable retail DeFi users to access institutional-grade yield strategies through a pooling
protocol that aggregates deposits and socializes gas costs. This reduces individual
transaction costs by 60% while improving average yields by 2-4%, addressing the primary
barrier to DeFi adoption for users with <$10K in capital.
```

### Problem Statement / Motivation

**Purpose:** Convince reviewers the problem is real, painful, and worth solving.

Structure as three movements: **Current State** (what users do today), **User Pain** (what's wrong with it), and **Impact** (why it matters for users and the business). Make the pain concrete with real user data—quantify whenever possible.

```markdown
❌ Vague pain:

DeFi is hard to use and expensive for small users. Many people give up.

✅ Concrete, narrative pain:

Users with less than $10K in capital face a 3-5% annual drag from gas fees alone when
managing DeFi positions across multiple protocols. Our research (Q4 2025, n=150) reveals
a stark pattern: 67% of small holders check rates daily but rebalance less than once a
month because gas costs eat their margins. The average user spends $400-600/year in gas
to manage roughly $5K in capital—making active management economically irrational. As a
result, 43% abandon DeFi entirely within six months, citing "too expensive for small
amounts." This represents a $2.4B addressable market of small holders who want DeFi
yields but are priced out by current economics.
```

Notice how the narrative version chains each fact to the next: the gas drag _causes_ infrequent rebalancing, which _leads to_ irrational economics, which _results in_ abandonment, which _represents_ an untapped market. Each sentence earns the next.

**Full example:**

```markdown
## Problem Statement

### Current State

Individual DeFi users interact directly with lending protocols (Aave, Compound), DEXes
(Uniswap), and yield farms (Curve, Convex) to earn yield on their crypto assets. Each
interaction requires a separate transaction and gas fee.

### User Pain

This direct interaction model creates three compounding problems. First, users pay
$5-50 per transaction depending on congestion, which for those with under $10K in capital
translates to 3-5% annual drag—more than many protocols yield. Second, optimizing returns
requires monitoring 8-12 protocols and understanding complex risk trade-offs; our research
shows 78% of retail users lack confidence to do this effectively. Third, because
institutional players access 4-6% higher APYs through automated strategies and batched
execution, retail users systematically leave value on the table.

These three factors compound: high costs discourage active management, which prevents
learning, which widens the gap with institutional returns.

### Impact

Small holders ($1K-$10K) are effectively excluded from optimal DeFi yields, creating a
"rich get richer" dynamic that undermines DeFi's accessibility promise. Meanwhile, 2.4M
wallet addresses hold $1K-$10K in DeFi-compatible assets but don't actively use yield
protocols—$8.2B in dormant capital representing untapped demand.
```

### Goals and Success Metrics

**Purpose:** Define what success looks like, with measurable outcomes that trace back to user value.

Every business metric should connect to user value. Don't just say "increase TVL"—explain why TVL growth indicates you're solving user problems. Be specific about targets and measurement methods.

```markdown
❌ Vague goals:

- Improve user experience
- Increase engagement
- Grow revenue

✅ Goals tied to user value:

This product succeeds when small holders can participate in DeFi yield strategies without
gas costs eating their returns.

For users, that means reducing annual gas drag from 3-5% to under 0.5%, earning 2-4%
higher APY through optimized allocation, and replacing 8-12 manual rebalances with a
single deposit transaction.

For the business, we target activating 20% of dormant small holders ($1K-$10K) within
6 months and reaching $50M TVL within 12 months—both signals that we're genuinely
solving the access problem, not just attracting speculative capital.

We measure this through on-chain gas comparison (target: $400-600/year saved per user),
pool APY vs. self-directed APY (target: 2-4% improvement via backtest + live data), and
user surveys on time spent (target: from 60 min/week to under 5 min/week).
```

### User Personas / Target Audience

**Purpose:** Ensure we're designing for real users with specific needs, not abstract personas.

Describe who the users are, what drives their behavior today, and what they need from this product. Differentiate segments by what matters: their constraints, motivations, and current workarounds.

```markdown
## Target Audience

### Primary: Small-Capital DeFi Users

These users hold $1K-$10K in crypto, understand DeFi basics (they've used a DEX and know
what APY means), but sit on the sidelines. They check DeFi rates regularly but rarely act
because gas costs make small transactions uneconomical. They want better returns than
centralized alternatives like Coinbase Earn, but without the active management burden.
Their core need is one-click simplicity: deposit once, let the system optimize, withdraw
whenever they want with clear fee disclosure.

### Secondary: Crypto-Curious Traditional Investors

These users hold $5K-$50K, may have bought crypto on Coinbase, but find DeFi intimidating.
They're aware DeFi offers better yields but don't trust themselves to navigate it safely.
They need a dead-simple experience comparable to Coinbase Earn, with clear risk disclosures
and social proof (audits, TVL figures, user testimonials) to build confidence.
```

### Proposed Solution

**Purpose:** Describe your solution at a level where reviewers can evaluate the approach without getting lost in technical details. This is the "product view"—smart contract architecture, API designs, and database schemas belong in the technical spec.

```markdown
## Proposed Solution

### Overview

A DeFi pooling protocol that aggregates user deposits and deploys them across multiple
yield-generating protocols with automated rebalancing. Users deposit stablecoins in a
single transaction, receive pool tokens representing their share, and the system handles
everything else.

### How It Works

Users connect their wallet, select a stablecoin and amount, and deposit in one
transaction. They receive ERC20 pool tokens representing their ownership percentage. The
pool automatically allocates across 3-5 protocols based on risk-adjusted APY, rebalancing
every 6 hours when yield spreads exceed the gas cost threshold (>0.5% APY difference).
Because all users' deposits are batched, gas costs are socialized rather than individual.

To withdraw, users burn their pool tokens and receive their proportional share within
1-2 blocks. Withdrawal gas is individualized (users pay their own exit cost).

### Why This Solves the Problem

Pooling eliminates the gas barrier because users only pay gas on deposit and withdrawal,
not ongoing management—reducing gas drag from 3-5% to under 0.5% for anyone holding 6+
months. It removes complexity because users never choose protocols or trigger rebalances.
And it unlocks better yields because pool size enables strategies unavailable to small
holders (e.g., Curve LP positions requiring >$50K for gas efficiency).
```

### Requirements

**Purpose:** Specify what the product must do, should do, and won't do. Use **MoSCoW prioritization** to set clear expectations about scope.

Requirements use checklists because they _are_ discrete items—this is where bullet points earn their place. Include a "Won't Have" section to explicitly bound scope and prevent feature creep.

```markdown
## Requirements

### Must Have (P0 - Launch Blockers)

- [ ] Single-transaction deposit for USDC, USDT, and DAI
- [ ] ERC20 pool tokens representing proportional ownership
- [ ] Anytime withdrawal by burning pool tokens
- [ ] Automated allocation across Aave, Compound, Curve with risk-adjusted rebalancing
- [ ] Dashboard showing allocation breakdown, historical APY (7d/30d/90d), gas savings
- [ ] Smart contracts audited by 2+ firms, emergency pause with guaranteed exit

### Should Have (P1 - Post-Launch)

- [ ] Additional stablecoins (FRAX, sUSD)
- [ ] Auto-compounding of yield
- [ ] Mobile-optimized web interface

### Could Have (P2 - Future)

- [ ] Non-stablecoin assets (ETH, WBTC)
- [ ] User-configurable risk profiles
- [ ] Governance token for parameter voting

### Won't Have (Explicit Non-Goals)

- ❌ Lending/borrowing (pure yield aggregation only)
- ❌ Cross-chain deposits (single chain MVP)
- ❌ Leveraged strategies (no debt positions)
- ❌ Fiat on/off ramps (users must already hold stablecoins)
```

### Assumptions and Constraints

**Purpose:** Document what you're assuming to be true and what's fixed. State assumptions clearly enough that reviewers can challenge them—if an assumption breaks, the team should know which parts of the plan are affected.

```markdown
## Assumptions

We assume users prefer simplicity over control (willing to let the algorithm allocate),
that gas prices remain below 200 gwei on average (above that, unit economics break), and
that DeFi yield rates stay at least 2% above centralized savings alternatives.

## Constraints

We're building for EVM only, with a team of 4 engineers over 6 months. The $200K audit
budget limits contract complexity, and regulatory constraints require geo-blocking for
restricted jurisdictions and GDPR compliance for EU users.
```

### Alternatives Considered

**Purpose:** Show reviewers you've explored options and chosen deliberately. For each alternative, explain the approach, its trade-offs, and why you didn't choose it.

```markdown
### Alternative: Frontend-Only Yield Aggregator (No Pooling)

We considered building a comparison UI that helps users find the best rates but leaves
them to execute transactions individually. This would be simpler to build (no smart
contracts) and carry no contract risk. However, it doesn't solve the core pain: users
would still pay gas per transaction, still be limited by their capital size, and we'd
be competing with existing aggregators without differentiation. We rejected this because
it addresses the information problem but not the economic one.

### Alternative: Integrate Existing Vaults (Yearn, Beefy)

Building on top of existing vault protocols would get us to market faster with
battle-tested infrastructure. But existing vaults target larger capital ($10K+), accept
higher risk strategies than our users want, and their fee structure (vault fees + our
fees) would erode the cost savings we're promising. We need custom allocation logic
optimized for small-holder economics.

### Alternative: Do Nothing

User research shows 78% of small holders want a solution but won't use existing tools.
The $8.2B in dormant capital confirms unmet demand worth pursuing.
```

### Risks and Mitigations

**Purpose:** Show you've anticipated what could go wrong and have a plan for each scenario.

Use a risk matrix for scannability, but ensure each mitigation is specific and actionable:

```markdown
## Risks and Mitigations

| Risk                     | Likelihood | Impact   | Mitigation                                                                                                       |
| ------------------------ | ---------- | -------- | ---------------------------------------------------------------------------------------------------------------- |
| Smart contract exploit   | Medium     | Critical | 2+ independent audits, $500K bug bounty, staged TVL cap ($5M for 3 months), emergency pause with guaranteed exit |
| Integrated protocol hack | Low        | High     | Diversify across 3+ protocols, real-time health monitoring, ability to remove protocol from allocation           |
| Poor adoption (<$5M TVL) | Medium     | High     | Pre-launch waitlist validation (5K target), liquidity mining incentives, distribution partnerships               |
| Gas price spike          | Medium     | Medium   | Dynamic fee structure, L2 deployment option, adjustable minimum deposit                                          |
| Regulatory action        | Low        | Critical | Legal review per jurisdiction, geo-blocking, decentralized governance path                                       |
```

### Diagrams and Visual Aids

Use diagrams when they clarify user flows, before/after comparisons, or system architecture. Don't use them when text would be clearer, the diagram has only 2-3 elements, or you're filling space.

The most valuable diagram in a PRD is a **before/after comparison** that makes the impact visceral—showing 10 steps reduced to 2 communicates value faster than any paragraph. Use mermaid for flow diagrams and keep them focused on the user journey, not implementation details.

---

## Common Mistakes

### Problem Statement

| Mistake             | Example                      | Fix                                                      |
| ------------------- | ---------------------------- | -------------------------------------------------------- |
| Vague pain          | "DeFi is hard"               | Quantify: "67% abandon within 6 months due to gas costs" |
| Solution in problem | "We need a pooling protocol" | State user pain: "Users can't afford gas fees"           |
| No user evidence    | "Users probably want this"   | Cite research: "User interviews (n=50) found..."         |
| Assumed knowledge   | "The gas cost issue"         | Explain: "$5-50 per transaction"                         |

### Goals and Metrics

| Mistake          | Example              | Fix                                                |
| ---------------- | -------------------- | -------------------------------------------------- |
| Vanity metrics   | "Increase sign-ups"  | User value: "Reduce gas costs by 60%"              |
| No targets       | "Grow TVL"           | Specific: "$50M TVL by month 12"                   |
| Unmeasurable     | "Improve UX"         | Proxy: "Reduce time-to-deposit from 10min to 2min" |
| Missing baseline | "Increase retention" | Compare: "From 40% to 60% 6-month retention"       |

### Requirements

| Mistake             | Example             | Fix                                          |
| ------------------- | ------------------- | -------------------------------------------- |
| Too detailed        | Function signatures | High-level: "User can deposit and withdraw"  |
| No prioritization   | Everything is P0    | Use MoSCoW: Must/Should/Could/Won't          |
| Implementation leak | "Use PostgreSQL"    | Outcome: "Data persists reliably"            |
| Ambiguous           | "Good performance"  | Specific: "Withdrawals complete <30 seconds" |

### Narrative

| Mistake              | Fix                                                     |
| -------------------- | ------------------------------------------------------- |
| Bullet-only sections | Prose to connect ideas; bullets only for discrete lists |
| No user empathy      | Start with user perspective: "Users today..."           |
| Missing the "why"    | Every feature traces back to user pain                  |
| Jargon overload      | Define terms or link to glossary                        |

---

## PRD Checklist

Use this before submitting for review.

### Structure and Clarity

- [ ] Summary is 3-4 sentences (problem + solution + value)
- [ ] Problem statement uses concrete data, not assumptions
- [ ] Goals are specific, measurable, and tied to user value
- [ ] Target personas reflect real user segments
- [ ] Solution is at product level, not implementation level
- [ ] Requirements use MoSCoW prioritization
- [ ] Non-goals explicitly bound scope

### Narrative Quality

- [ ] Each section flows logically to the next (problem → solution → impact)
- [ ] Prose explains reasoning; bullets reserved for discrete lists
- [ ] A non-expert could understand the user problem
- [ ] All claims backed by data or research
- [ ] Technical terms defined or linked

### Completeness

- [ ] Success metrics have targets and measurement methods
- [ ] Risks have specific, actionable mitigations
- [ ] Alternatives considered with clear rationale for chosen approach
- [ ] Assumptions stated clearly enough to challenge
- [ ] Diagrams add value (not decoration)

### Ready for Review

- [ ] Re-read as a stakeholder from another team
- [ ] Narrative arc is coherent (would pass the ABT test)
- [ ] Can defend why this solution beats alternatives
- [ ] Success metrics are realistic and measurable
