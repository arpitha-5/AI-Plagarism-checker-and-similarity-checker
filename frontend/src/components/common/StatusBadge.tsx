import type { ReactNode } from 'react'
export function StatusBadge({ children, tone = 'info' }: { children: ReactNode; tone?: string }) { return <span className={`status-badge status-badge-${tone}`}>{children}</span> }
