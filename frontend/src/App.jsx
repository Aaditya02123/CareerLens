import { useEffect, useState } from 'react'

function App() {
  const [backendStatus, setBackendStatus] = useState('loading')

  useEffect(() => {
    fetch('http://127.0.0.1:8000/health')
      .then((response) => {
        if (!response.ok) {
          throw new Error(`Request failed with status ${response.status}`)
        }

        return response.json()
      })
      .then((data) => setBackendStatus(data.status))
      .catch(() => setBackendStatus('unavailable'))
  }, [])

  return (
    <main className="flex min-h-screen items-center justify-center bg-slate-950 px-6 text-slate-50">
      <section className="max-w-xl text-center">
        <p className="mb-4 text-sm font-semibold uppercase tracking-[0.2em] text-sky-300">
          CareerLens
        </p>
        <h1 className="text-4xl font-bold tracking-tight sm:text-5xl">
          CareerLens
        </h1>
        <p className="mt-5 text-lg text-slate-300">
          AI-powered career intelligence platform
        </p>
        <p className="mt-8 text-sm text-emerald-300">
          Frontend is running.
        </p>
        <p className="mt-3 text-sm text-slate-300">
          Backend status:{' '}
          <span className="font-semibold text-sky-300">{backendStatus}</span>
        </p>
      </section>
    </main>
  )
}

export default App
