import { useId } from 'react'

/** Vector fallback shares the live scene's composition; no GPU or animation. */
export function StaticOrb() {
  const prefix = useId().replaceAll(':', '')
  const id = (name: string) => `${prefix}-${name}`
  return <svg className="orb-static" viewBox="0 0 600 600" aria-hidden="true" focusable="false" data-testid="orb-static">
    <defs>
      <radialGradient id={id('glass')} cx="30%" cy="20%" r="85%">
        <stop stopColor="#ddffff" stopOpacity=".5" /><stop offset=".3" stopColor="#39c9e0" stopOpacity=".08" />
        <stop offset=".72" stopColor="#0a506d" stopOpacity=".12" /><stop offset="1" stopColor="#b9fffa" stopOpacity=".52" />
      </radialGradient>
      <linearGradient id={id('rim')} x1="0" x2="1" y2="1"><stop stopColor="#efffff" /><stop offset=".25" stopColor="#7bfff7" stopOpacity=".15" /><stop offset=".7" stopColor="#6ce1e5" stopOpacity=".3" /><stop offset="1" stopColor="#fff1d9" /></linearGradient>
      <linearGradient id={id('pill')} x1="0" x2="1"><stop stopColor="var(--capsule-dark, #087b91)" /><stop offset=".35" stopColor="var(--capsule-light, #8dfbf1)" /><stop offset=".7" stopColor="var(--capsule-mid, #209db4)" /><stop offset="1" stopColor="var(--capsule-deep, #034d70)" /></linearGradient>
      <linearGradient id={id('white')} x1="0" x2="1"><stop stopColor="#8cbed1" /><stop offset=".4" stopColor="#fcffff" /><stop offset=".8" stopColor="#c5eff2" /><stop offset="1" stopColor="#447f97" /></linearGradient>
      <linearGradient id={id('shine')} x1="0" x2="1"><stop stopColor="white" stopOpacity="0" /><stop offset=".5" stopColor="white" stopOpacity=".8" /><stop offset="1" stopColor="white" stopOpacity="0" /></linearGradient>
      <filter id={id('soft')}><feGaussianBlur stdDeviation="5" /></filter>
    </defs>
    <g transform="rotate(-28 300 300)">
      <ellipse cx="300" cy="300" rx="192" ry="220" fill={`url(#${id('glass')})`} stroke={`url(#${id('rim')})`} strokeWidth="1.5" />
      <ellipse cx="300" cy="300" rx="220" ry="195" fill="none" stroke={`url(#${id('rim')})`} strokeWidth="1.5" transform="rotate(53 300 300)" />
      <ellipse cx="300" cy="300" rx="225" ry="112" fill="none" stroke={`url(#${id('rim')})`} transform="rotate(-30 300 300)" />
      <path d="M174 158c-64 52-70 171-25 246" fill="none" stroke="#c6ffff" strokeOpacity=".6" strokeWidth="6" filter={`url(#${id('soft')})`} />
      <rect x="246" y="171" width="108" height="258" rx="54" fill={`url(#${id('white')})`} stroke="#ddffff" strokeWidth="1.5" />
      <path d="M246 300V225a54 54 0 0 1 108 0v75Z" fill={`url(#${id('pill')})`} />
      <path d="M247 299h106" stroke="#c7ffff" strokeOpacity=".8" />
      <rect x="260" y="189" width="19" height="204" rx="9" fill={`url(#${id('shine')})`} opacity=".8" />
      <path d="M177 143c35-33 100-50 147-41" fill="none" stroke="#edffff" strokeWidth="3" strokeLinecap="round" />
    </g>
  </svg>
}
