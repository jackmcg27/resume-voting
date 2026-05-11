import { useState, useEffect, useRef, useCallback } from 'react'

export function useSessionWS(sessionCode, name = null) {
  const [session, setSession] = useState(null)
  const [connected, setConnected] = useState(false)
  const wsRef = useRef(null)
  const clientIdRef = useRef(crypto.randomUUID())
  const nameRef = useRef(name)
  nameRef.current = name

  const send = useCallback((msg) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify(msg))
    }
  }, [])

  useEffect(() => {
    if (!sessionCode) return

    let cancelled = false
    let timer = null

    const connect = () => {
      if (cancelled) return
      const proto = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
      const url = `${proto}//${window.location.host}/ws/${sessionCode}/${clientIdRef.current}`
      const ws = new WebSocket(url)
      wsRef.current = ws

      ws.onopen = () => {
        if (cancelled) return
        setConnected(true)
        if (nameRef.current) {
          ws.send(JSON.stringify({ type: 'join', name: nameRef.current }))
        }
      }

      ws.onclose = () => {
        if (cancelled) return
        setConnected(false)
        timer = setTimeout(connect, 2000)
      }

      ws.onerror = () => ws.close()

      ws.onmessage = (e) => {
        try {
          const msg = JSON.parse(e.data)
          if (msg.type === 'state') setSession(msg.session)
        } catch (_) {}
      }
    }

    connect()

    return () => {
      cancelled = true
      clearTimeout(timer)
      wsRef.current?.close()
    }
  }, [sessionCode])

  return { session, connected, send }
}
