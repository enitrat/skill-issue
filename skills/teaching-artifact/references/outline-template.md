# Outline template

Send this in chat before writing any HTML. Fill every `<…>`. One sentence per line.

```md
Your goal: <what the reader must do after reading, one sentence>. Here is the outline; I'm holding the page until you approve it.

## Reader
- Who: <role(s), e.g. "the SDK team" / "a product person and an engineer">.
- Already knows: <what we can assume>. Does not know: <what we must define>.
- Baseline they compare against: <repo, branch or version, read on <date>> (or "none").

## Spine (<branch from SKILL.md section 2>)
**L0 Short answer.** <verdict sentence | 3 lines of code | diagram + sentence>.
**L1 Context.** Goal / Who it's for / Material: <repo, PR, branch, date>.
**2. <Section>** (<Diátaxis mode>). Answer: "<sentence>". Visual: <stepper of N steps | Today/Proposed tabs | before/after over areas A, B, C | matrix | table>. Folds: <what>.
… one line per section …
**N. Open questions.** Product vs Engineering.
**N+1. Reference.** Folds: <what>.

## Cut list
- <What the page will not contain, e.g. "how we got here", "the rejected candidates", "the app's flow engine in usage examples">.

## Voice and look
- Density: answer sentence + one caption per visual, ≤ 3 sentences per paragraph, < 900 visible words; detail in folds.
- Terms defined on first use: <the newcomer terms you already know you'll need>.
- Colours and fonts: <named design system and its files | quickstart defaults>. Light theme.

## Questions
1. <A question whose answer changes what you build.>
2. <…>
3. <…>
```

Why each part is there:
- **Reader and baseline** come first because the most expensive rewrites came from the wrong audience or the wrong "today".
- **The cut list** lets the user correct density before a page exists; users judge what is missing as easily as what is present.
- **Answer sentences per section** let the user judge content before design exists.
- Questions are limited to three; each must change what you build.
