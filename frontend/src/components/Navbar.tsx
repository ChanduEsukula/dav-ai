import type { ActivePage, ActiveSection } from '../types/navigation'

type NavbarProps = {
  activePage: ActivePage
  activeSection: ActiveSection
  goHome: () => void
  goToRecallRadar: () => void
  goToDrugSignal: () => void
  goToPage: (page: ActivePage) => void
}

function Navbar({
  activePage,
  activeSection,
  goHome,
  goToRecallRadar,
  goToDrugSignal,
  goToPage,
}: NavbarProps) {
  return (
    <nav className="nav">
      <button className="brand brand-button" onClick={goHome}>
        <span className="brand-mark">✚</span>
        <span>Dav AI</span>
      </button>

      <div className="nav-links">
        <button
          className={activePage === 'home' && activeSection === 'home' ? 'active' : ''}
          onClick={goHome}
        >
          Home
        </button>

        <button
          className={activePage === 'home' && activeSection === 'recallradar' ? 'active' : ''}
          onClick={goToRecallRadar}
        >
          RecallRadar
        </button>

        <button
          className={activePage === 'home' && activeSection === 'drugsignal' ? 'active' : ''}
          onClick={goToDrugSignal}
        >
          DrugSignal
        </button>

        <button
          className={activePage === 'sources' ? 'active' : ''}
          onClick={() => goToPage('sources')}
        >
          Sources
        </button>

        <button
          className={activePage === 'audit' ? 'active' : ''}
          onClick={() => goToPage('audit')}
        >
          Audit
        </button>

        <button
          className={activePage === 'system' ? 'active' : ''}
          onClick={() => goToPage('system')}
        >
          System
        </button>

        <button
          className={activePage === 'saved-monitors' ? 'active' : ''}
          onClick={() => goToPage('saved-monitors')}
        >
          Monitors
        </button>

        <button
          className={activePage === 'regional-health' ? 'active' : ''}
          onClick={() => goToPage('regional-health')}
        >
          Health Pulse
        </button>

        <button className={activePage === 'about' ? 'active' : ''} onClick={() => goToPage('about')}>
          About
        </button>

        <button className={activePage === 'faq' ? 'active' : ''} onClick={() => goToPage('faq')}>
          FAQ
        </button>

        <button className={activePage === 'help' ? 'active' : ''} onClick={() => goToPage('help')}>
          Help
        </button>
      </div>
    </nav>
  )
}

export default Navbar
