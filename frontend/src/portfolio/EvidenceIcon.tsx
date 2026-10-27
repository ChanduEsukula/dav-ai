export type EvidenceKind = 'labels' | 'recalls' | 'faers'

export function EvidenceIcon({ kind }: { kind: EvidenceKind }) {
  return <svg viewBox="0 0 32 32" fill="none" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true" focusable="false">
    {kind === 'labels' ? <><path d="M10 4h10l6 6v18H7V7a3 3 0 0 1 3-3Z" /><path d="M19 4v7h7M12 16h9M12 21h9M12 11h2" /></>
      : kind === 'recalls' ? <><path d="m16 4 12 23H4L16 4Z" /><path d="M16 12v7M16 23h.01" /></>
        : <><rect x="5" y="18" width="5" height="10" rx="1.5" /><rect x="14" y="11" width="5" height="17" rx="1.5" /><rect x="23" y="4" width="5" height="24" rx="1.5" /></>}
  </svg>
}
