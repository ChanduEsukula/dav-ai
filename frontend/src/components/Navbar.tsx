import {
  INFORMATION_NAV_PAGE_IDS,
  OPERATIONS_NAV_PAGE_IDS,
  PAGE_IDS,
  PAGE_METADATA,
  PRIMARY_NAV_PAGE_IDS,
  type ActivePage,
} from '../types/navigation'

type NavbarProps = {
  activePage: ActivePage
  goHome: () => void
  goToPage: (page: ActivePage) => void
}

type NavItem = {
  id: ActivePage
  label: string
  isActive: boolean
  onClick: () => void
}

function Navbar({
  activePage,
  goHome,
  goToPage,
}: NavbarProps) {
  const createNavItems = (pageIds: readonly ActivePage[]): NavItem[] =>
    pageIds.map((pageId) => ({
      id: pageId,
      label: PAGE_METADATA[pageId].label,
      isActive: activePage === pageId,
      onClick: pageId === PAGE_IDS.HOME ? goHome : () => goToPage(pageId),
    }))

  const primaryNavItems = createNavItems(PRIMARY_NAV_PAGE_IDS)
  const operationsNavItems = createNavItems(OPERATIONS_NAV_PAGE_IDS)
  const secondaryNavItems = createNavItems(INFORMATION_NAV_PAGE_IDS)

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

      <div className="nav-links" aria-label="Main pages">
        {primaryNavItems.map(renderNavItem)}
      </div>

      <div className="nav-links nav-links-secondary" aria-label="Advanced operations">
        {operationsNavItems.map(renderNavItem)}
      </div>

      <div className="nav-links nav-actions" aria-label="Information pages">
        {secondaryNavItems.map(renderNavItem)}
      </div>
    </nav>
  )
}

export default Navbar
