import { useState, useEffect } from 'react'
import StoredDrugCatalog from './components/StoredDrugCatalog'
import Workspace from './research/Workspace'
import ExperienceSelector from './components/ExperienceSelector'
import {
  type ExperienceMode,
  getInitialExperienceMode,
} from './components/experienceState'
import './theme.css'
import './App.css'

export default function App() {
  const [mode, setMode] = useState<ExperienceMode>(getInitialExperienceMode)
  const ask = window.location.pathname === '/ask'

  useEffect(() => {
    document.documentElement.setAttribute('data-theme', mode)
  }, [mode])

  return (
    <div className="app-container" data-theme={mode}>
      <header className="app-nav-bar workspace-nav">
        <div className="app-brand-group">
          <a className="app-brand-link" href="/">
            Dav AI
            <span className="app-brand-subtitle">
              {mode === 'everyday' ? 'Medication Guide' : 'Evidence Research Pro'}
            </span>
          </a>

          <nav aria-label="Workspace navigation" className="app-route-links">
            <a href="/" aria-current={!ask ? 'page' : undefined}>
              Evidence explorer
            </a>
            <a href="/ask" aria-current={ask ? 'page' : undefined}>
              Ask Dav AI
            </a>
          </nav>
        </div>

        <ExperienceSelector mode={mode} onChange={setMode} />
      </header>

      {ask ? <Workspace mode={mode} /> : <StoredDrugCatalog />}
    </div>
  )
}
