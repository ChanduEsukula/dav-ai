import type { ActivePage, ActiveSection } from '../types/navigation'

type NavbarProps = {
  activePage: ActivePage
  activeSection: ActiveSection
  goHome: () => void
  goToRecallRadar: () => void
  goToDrugSignal: () => void
  goToPage: (page: ActivePage) => void
}

type NavItem = {
  id: string
  label: string
  isActive: boolean
  onClick: () => void
}

function Navbar({
  activePage,
  activeSection,
  goHome,
  goToRecallRadar,
  goToDrugSignal,
  goToPage,
}: NavbarProps) {
  const isHomeActive = activePage === 'home' && activeSection === 'home'

  const primaryNavItems: NavItem[] = [
    {
      id: 'home',
      label: 'Home',
      isActive: isHomeActive,
      onClick: goHome,
    },
    {
      id: 'recallradar',
      label: 'RecallRadar',
      isActive: activePage === 'home' && activeSection === 'recallradar',
      onClick: goToRecallRadar,
    },
    {
      id: 'drugsignal',
      label: 'DrugSignal',
      isActive: activePage === 'home' && activeSection === 'drugsignal',
      onClick: goToDrugSignal,
    },
    {
      id: 'regional-health',
      label: 'Health Pulse',
      isActive: activePage === 'regional-health',
      onClick: () => goToPage('regional-health'),
    },
    {
      id: 'saved-monitors',
      label: 'Monitors',
      isActive: activePage === 'saved-monitors',
      onClick: () => goToPage('saved-monitors'),
    },
  ]

  const operationsNavItems: NavItem[] = [
    {
      id: 'audit',
      label: 'Audit',
      isActive: activePage === 'audit',
      onClick: () => goToPage('audit'),
    },
    {
      id: 'sources',
      label: 'Sources',
      isActive: activePage === 'sources',
      onClick: () => goToPage('sources'),
    },
    {
      id: 'system',
      label: 'System',
      isActive: activePage === 'system',
      onClick: () => goToPage('system'),
    },
  ]

  const secondaryNavItems: NavItem[] = [
    {
      id: 'about',
      label: 'About',
      isActive: activePage === 'about',
      onClick: () => goToPage('about'),
    },
    {
      id: 'faq',
      label: 'FAQ',
      isActive: activePage === 'faq',
      onClick: () => goToPage('faq'),
    },
    {
      id: 'help',
      label: 'Help',
      isActive: activePage === 'help',
      onClick: () => goToPage('help'),
    },
  ]

  const renderNavItem = (item: NavItem) => (
    <button
      key={item.id}
      type="button"
      className={item.isActive ? 'active' : ''}
      aria-current={item.isActive ? 'page' : undefined}
      onClick={item.onClick}
    >
      {item.label}
    </button>
  )

  return (
    <nav className="nav" aria-label="Main navigation">
      <button
        type="button"
        className="brand brand-button"
        aria-current={isHomeActive ? 'page' : undefined}
        onClick={goHome}
      >
        <span className="brand-mark" aria-hidden="true">
          ✚
        </span>
        <span>Dav AI</span>
      </button>

      <div className="nav-links" aria-label="Navigation groups">
        <div className="nav-group nav-group-primary" aria-label="Primary product navigation">
          {primaryNavItems.map(renderNavItem)}
        </div>

        <div className="nav-group nav-group-operations" aria-label="Trust and operations">
          {operationsNavItems.map(renderNavItem)}
        </div>

        <div className="nav-group nav-group-secondary" aria-label="Help and information">
          {secondaryNavItems.map(renderNavItem)}
        </div>
      </div>
    </nav>
  )
}

export default Navbar