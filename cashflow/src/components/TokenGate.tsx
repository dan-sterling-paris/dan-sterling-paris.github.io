import { useState } from 'react'

interface TokenGateProps {
  onAuth: () => void
}

async function hashPassword(password: string): Promise<string> {
  const encoder = new TextEncoder()
  const data = encoder.encode(password)
  const hashBuffer = await crypto.subtle.digest('SHA-256', data)
  const hashArray = Array.from(new Uint8Array(hashBuffer))
  return hashArray.map((b) => b.toString(16).padStart(2, '0')).join('')
}

export default function TokenGate({ onAuth }: TokenGateProps) {
  const [password, setPassword] = useState('')
  const [error, setError] = useState(false)
  const [checking, setChecking] = useState(false)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setChecking(true)
    setError(false)

    const hash = await hashPassword(password)
    const expectedHash = import.meta.env.VITE_ACCESS_TOKEN_HASH as string

    if (hash === expectedHash) {
      localStorage.setItem('cashflow_auth', 'true')
      onAuth()
    } else {
      setError(true)
      setPassword('')
    }
    setChecking(false)
  }

  return (
    <div className="min-h-screen bg-[#1a1a2e] flex items-center justify-center p-4">
      <form
        onSubmit={handleSubmit}
        className="bg-gray-900 rounded-xl p-8 w-full max-w-sm flex flex-col gap-4"
      >
        <h1 className="text-white text-2xl font-semibold text-center">
          Cashflow
        </h1>
        <input
          type="password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          placeholder="Enter password"
          className="w-full bg-gray-800 text-white border border-gray-700 rounded-lg px-4 py-3 outline-none focus:border-blue-500 transition-colors"
          autoFocus
        />
        {error && (
          <p className="text-red-400 text-sm text-center">
            Incorrect password. Please try again.
          </p>
        )}
        <button
          type="submit"
          disabled={checking || !password}
          className="bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-white font-medium rounded-lg px-4 py-3 transition-colors"
        >
          {checking ? 'Checking...' : 'Unlock'}
        </button>
      </form>
    </div>
  )
}
