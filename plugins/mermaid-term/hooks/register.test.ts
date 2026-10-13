import { expect, test } from 'claude-code/testing'

import { rewrite } from './register'

const draw = async (s: string) => (s.includes('bad') ? null : `[${s.trim()}]`)

test('swaps closed mermaid fences, keeps failures, wide art and unclosed fences', async () => {
  const text = 'a\n```mermaid\ngraph TD\n```\nb\n```mermaid\nbad\n```\n```mermaid\nopen'
  expect(await rewrite(text, 80, draw)).toBe(
    'a\n```text\n[graph TD]\n```\nb\n```mermaid\nbad\n```\n```mermaid\nopen',
  )
  expect(await rewrite('```mermaid\ngraph TD\n```', 3, draw)).toBe('```mermaid\ngraph TD\n```')
})
