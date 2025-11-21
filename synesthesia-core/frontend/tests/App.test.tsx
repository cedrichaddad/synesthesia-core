import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import Page from '../app/page'

// Mock the LabWorkbench component since it has complex dependencies
vi.mock('../components/LabWorkbench', () => ({
    default: () => <div data-testid="lab-workbench">Lab Workbench</div>
}))

describe('App', () => {
    it('renders the LabWorkbench', () => {
        render(<Page />)
        expect(screen.getByTestId('lab-workbench')).toBeInTheDocument()
    })
})
