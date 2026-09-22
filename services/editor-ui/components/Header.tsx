import Link from 'next/link'

export default function Header() {
  return (
    <header className="bg-slate-50 border-b border-slate-100">
      <div className="container py-4 flex items-center justify-between">
        <div className="flex items-center gap-4">
          <svg width="40" height="40" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg"><rect width="24" height="24" rx="4" fill="#0f172a"/></svg>
          <div>
            <div className="header-brand">STEMpathize Digest</div>
            <div className="text-sm text-slate-500">Data-driven, empathy-aware synthesis</div>
          </div>
        </div>
        <nav className="space-x-4 text-sm">
          <Link href="/">Dashboard</Link>
          <a href="/editor/" className="text-slate-600">Editor</a>
        </nav>
      </div>
    </header>
  )
}
