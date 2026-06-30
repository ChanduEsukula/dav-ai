import {
  ADVANCED_NAV_PAGE_IDS,
  PAGE_IDS,
  PAGE_METADATA,
  PRIMARY_NAV_PAGE_IDS,
  type ActivePage,
} from '../types/navigation'
import { useAuth } from '../auth/AuthContext'
import { useState } from 'react'

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
  const { currentUser, logout } = useAuth()
  const [advancedOpen, setAdvancedOpen] = useState(false)

  const createNavItems = (pageIds: readonly ActivePage[]): NavItem[] =>
    pageIds.map((pageId) => ({
      id: pageId,
      label: PAGE_METADATA[pageId].label,
      isActive: activePage === pageId,
      onClick: pageId === PAGE_IDS.HOME ? goHome : () => goToPage(pageId),
    }))

  const primaryNavItems = createNavItems(PRIMARY_NAV_PAGE_IDS)
  const advancedNavItems = createNavItems(ADVANCED_NAV_PAGE_IDS)
  const advancedPageIsActive = advancedNavItems.some((item) => item.isActive)

  function handleLogout() {
    logout()
    goToPage(PAGE_IDS.LOGIN)
  }

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

  const renderAdvancedNavItem = (item: NavItem) => (
    <button
      key={item.id}
      type="button"
      className={item.isActive ? 'active' : ''}
      aria-current={item.isActive ? 'page' : undefined}
      onClick={() => {
        item.onClick()
        setAdvancedOpen(false)
      }}
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

      <details
        className="nav-advanced"
        open={advancedOpen || advancedPageIsActive}
        onToggle={(event) => setAdvancedOpen(event.currentTarget.open)}
      >
        <summary
          className={advancedPageIsActive ? 'active' : ''}
          aria-current={advancedPageIsActive ? 'page' : undefined}
        >
          Workflows
        </summary>
        <div className="nav-advanced-menu" aria-label="Workflow pages">
          {advancedNavItems.map(renderAdvancedNavItem)}
        </div>
      </details>

      <div className="nav-links nav-actions" aria-label="Account actions">
        {currentUser ? (
          <>
            {renderNavItem({
              id: PAGE_IDS.PROFILE,
              label: 'Profile',
              isActive: activePage === PAGE_IDS.PROFILE,
              onClick: () => goToPage(PAGE_IDS.PROFILE),
            })}
            <button type="button" className="nav-logout-button" onClick={handleLogout}>
              Log out
            </button>
          </>
        ) : (
          <>
            {renderNavItem({
              id: PAGE_IDS.LOGIN,
              label: 'Log in',
              isActive: activePage === PAGE_IDS.LOGIN,
              onClick: () => goToPage(PAGE_IDS.LOGIN),
            })}
            {renderNavItem({
              id: PAGE_IDS.SIGNUP,
              label: 'Sign up',
              isActive: activePage === PAGE_IDS.SIGNUP,
              onClick: () => goToPage(PAGE_IDS.SIGNUP),
            })}
          </>
        )}
      </div>
    </nav>
  )
}

export default Navbar