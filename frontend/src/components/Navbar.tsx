import type { ActivePage } from '../types/navigation'

type NavbarProps = {
  activePage: ActivePage
  goHome: () => void
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
  goHome,
  goToPage,
}: NavbarProps) {
  const primaryNavItems: NavItem[] = [
    {
      id: 'home',
      label: 'Home',
      isActive: activePage === 'home',
      onClick: goHome,
    },
    {
      id: 'pharmacy-safety',
      label: 'Pharmacy Safety',
      isActive: activePage === 'pharmacy-safety',
      onClick: () => goToPage('pharmacy-safety'),
    },
    {
      id: 'food-safety',
      label: 'Food Safety',
      isActive: activePage === 'food-safety',
      onClick: () => goToPage('food-safety'),
    },
    {
      id: 'cosmetic-safety',
      label: 'Cosmetic Safety',
      isActive: activePage === 'cosmetic-safety',
      onClick: () => goToPage('cosmetic-safety'),
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
        onClick={goHome}
        aria-label="Dav AI home"
      >
        Dav AI
      </button>

      <div className="nav-links" aria-label="Primary modules">
        {primaryNavItems.map(renderNavItem)}
      </div>

      <div className="nav-links nav-links-secondary" aria-label="Operations">
        {operationsNavItems.map(renderNavItem)}
      </div>

      <div className="nav-links nav-actions" aria-label="Information pages">
        {secondaryNavItems.map(renderNavItem)}
      </div>
    </nav>
  )
}

export default Navbar
