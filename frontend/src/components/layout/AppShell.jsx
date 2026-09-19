import Sidebar from './Sidebar'
import Topbar from './Topbar'

function AppShell({
  activeSection,
  backendStatus,
  pageTitle,
  pageDescription,
  onNavigate,
  children,
}) {
  return (
    <div className="min-h-screen bg-[var(--cl-bg)] text-[var(--cl-text)]">
      <div className="flex min-h-screen flex-col lg:flex-row">
        <Sidebar
          activeSection={activeSection}
          onNavigate={onNavigate}
        />

        <div className="flex min-w-0 flex-1 flex-col">
          <Topbar
            title={pageTitle}
            description={pageDescription}
            backendStatus={backendStatus}
          />

          <main className="cl-scrollbar flex-1 overflow-x-hidden px-4 py-5 sm:px-6 lg:px-8 lg:py-8">
            <div className="mx-auto w-full max-w-7xl">{children}</div>
          </main>
        </div>
      </div>
    </div>
  )
}

export default AppShell