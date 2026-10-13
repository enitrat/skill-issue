import type { Register } from 'claude-code'

// Closed fences only: a fence still streaming in stays raw until its ``` lands.
const FENCE = /^```mermaid[^\n]*\n([\s\S]*?)\n```[ \t]*$/gm

export type Draw = (source: string) => Promise<string | null>

/** Replace each mermaid fence with a plain fence holding `draw`'s output; a null draw or one wider than `columns` keeps the source. */
export async function rewrite(text: string, columns: number, draw: Draw): Promise<string> {
  const fences = [...text.matchAll(FENCE)]
  if (fences.length === 0) return text
  const drawn = await Promise.all(fences.map(m => draw(m[1] ?? "")))
  let out = ''
  let at = 0
  fences.forEach((m, i) => {
    const art = drawn[i] ?? null
    const fits = art != null && art.split('\n').every(l => [...l].length <= columns)
    out += text.slice(at, m.index) + (fits ? '```text\n' + art + '\n```' : m[0])
    at = m.index + m[0].length
  })
  return out + text.slice(at)
}

export const register: Register = on => {
  // ponytail: unbounded per-process cache, add LRU if long sessions bloat
  const cache = new Map<string, Promise<string | null>>()

  on('ui.render', { component: 'AssistantMessage' }, async ($, e, next) => {
    if (!e.props.text.includes('```mermaid')) return next(e)

    const draw: Draw = source => {
      let hit = cache.get(source)
      if (!hit) {
        hit = $.process
          .run(['mmdflux', '-q', '--color', 'off'], { stdin: source, timeoutMs: 5000 })
          .then(r => (r.exitCode === 0 ? r.stdout.replace(/\s+$/, '') : null))
          .catch(() => null)
        cache.set(source, hit)
      }
      return hit
    }

    // Leave room for the reply bullet and fence padding.
    const columns = (e.viewport?.columns ?? 80) - 4
    const text = await rewrite(e.props.text, columns, draw)
    return next(text === e.props.text ? e : { ...e, props: { ...e.props, text } })
  })
}
