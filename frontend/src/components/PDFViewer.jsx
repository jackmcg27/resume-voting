import { useEffect, useRef, useState } from 'react'
import * as pdfjsLib from 'pdfjs-dist'

pdfjsLib.GlobalWorkerOptions.workerSrc = new URL(
  'pdfjs-dist/build/pdf.worker.min.mjs',
  import.meta.url,
).href

export default function PDFViewer({ url }) {
  const canvasRef = useRef(null)
  const renderTaskRef = useRef(null)
  const [pdf, setPdf] = useState(null)
  const [pageNum, setPageNum] = useState(1)
  const [numPages, setNumPages] = useState(0)
  const [scale, setScale] = useState(1.3)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  useEffect(() => {
    if (!url) return
    let cancelled = false
    setLoading(true)
    setError(null)
    setPdf(null)
    setPageNum(1)
    pdfjsLib.getDocument(url).promise.then((doc) => {
      if (!cancelled) {
        setPdf(doc)
        setNumPages(doc.numPages)
        setLoading(false)
      }
    }).catch((err) => {
      if (!cancelled) {
        setError('Failed to load PDF')
        setLoading(false)
      }
    })
    return () => { cancelled = true }
  }, [url])

  useEffect(() => {
    if (!pdf || !canvasRef.current) return
    let cancelled = false

    if (renderTaskRef.current) {
      renderTaskRef.current.cancel()
      renderTaskRef.current = null
    }

    pdf.getPage(pageNum).then((page) => {
      if (cancelled) return
      const viewport = page.getViewport({ scale })
      const canvas = canvasRef.current
      if (!canvas) return
      const ctx = canvas.getContext('2d')
      canvas.height = viewport.height
      canvas.width = viewport.width
      const task = page.render({ canvasContext: ctx, viewport })
      renderTaskRef.current = task
      task.promise.catch(() => {})
    })

    return () => { cancelled = true }
  }, [pdf, pageNum, scale])

  if (!url) return <div className="pdf-placeholder">No PDF selected</div>
  if (loading) return <div className="pdf-loading">Loading PDF…</div>
  if (error) return <div className="pdf-error">{error}</div>

  return (
    <div className="pdf-viewer">
      <div className="pdf-controls">
        <button onClick={() => setPageNum(p => Math.max(1, p - 1))} disabled={pageNum <= 1}>◀ Prev</button>
        <span className="page-info">Page {pageNum} / {numPages}</span>
        <button onClick={() => setPageNum(p => Math.min(numPages, p + 1))} disabled={pageNum >= numPages}>Next ▶</button>
        <span className="spacer" />
        <button onClick={() => setScale(s => Math.max(0.5, +(s - 0.25).toFixed(2)))} title="Zoom out">−</button>
        <span>{Math.round(scale * 100)}%</span>
        <button onClick={() => setScale(s => Math.min(3, +(s + 0.25).toFixed(2)))} title="Zoom in">+</button>
      </div>
      <div className="pdf-canvas-wrap">
        <canvas ref={canvasRef} />
      </div>
    </div>
  )
}
