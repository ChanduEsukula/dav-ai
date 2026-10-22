import StoredDrugCatalog from './components/StoredDrugCatalog'
import Workspace from './research/Workspace'
import './App.css'

export default function App() {
  const ask = window.location.pathname === '/ask'
  return <><nav aria-label="Workspace navigation" className="workspace-nav"><a href="/" aria-current={!ask ? 'page' : undefined}>Evidence explorer</a><a href="/ask" aria-current={ask ? 'page' : undefined}>Ask Dav AI</a></nav>{ask ? <Workspace /> : <StoredDrugCatalog />}</>
}
