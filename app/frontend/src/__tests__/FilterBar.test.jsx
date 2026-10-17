import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { FilterBar } from '../components/FilterBar'

function renderFilterBar(props = {}) {
  const handlers = {
    onToggleSpurs: vi.fn(),
    onToggleSpoiler: vi.fn(),
  }
  render(
    <FilterBar spursOnly={false} spoilerGuard={false} {...handlers} {...props} />
  )
  return handlers
}

describe('FilterBar（T-P3-13・F-14）', () => {
  it('TC-13-1: spursOnly=false で「Spursのみ」ボタンが存在する', () => {
    renderFilterBar()
    expect(screen.getByRole('button', { name: 'Spursのみ' })).toBeInTheDocument()
  })

  it('TC-13-2: 「全チーム」ボタンが存在する', () => {
    renderFilterBar()
    expect(screen.getByRole('button', { name: '全チーム' })).toBeInTheDocument()
  })

  it('TC-13-3: spursOnly=false で「Spursのみ」をクリックすると onToggleSpurs が1回呼ばれる', async () => {
    const user = userEvent.setup()
    const { onToggleSpurs } = renderFilterBar()
    await user.click(screen.getByRole('button', { name: 'Spursのみ' }))
    expect(onToggleSpurs).toHaveBeenCalledTimes(1)
  })
})
