import { useEffect, useState } from 'react'
import { io } from 'socket.io-client'

export function useSessionWS(sessionCode, name = null) {
  const [session, setSession] = useState(null)
  const [connected, setConnected] = useState(false)

  useEffect(() => {
    if (!sessionCode) return

    const socket = io()

    socket.on('connect', () => {
      setConnected(true)
      socket.emit('join_session', { code: sessionCode, name: name || null })
    })

    socket.on('state', (data) => setSession(data))
    socket.on('disconnect', () => setConnected(false))

    return () => socket.disconnect()
  }, [sessionCode, name])

  return { session, connected }
}
