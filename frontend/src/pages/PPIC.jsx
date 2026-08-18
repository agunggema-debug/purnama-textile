import { useState } from 'react'
import { useFetch } from '../hooks.js'
import { api } from '../api.js'

export default function PPIC() {
  return (
    <div>
      <h1>Modul PPIC — Perencanaan Produksi &amp; Persediaan</h1>
      <div className="grid" style={{ gridTemplateColumns: '1.4fr 1fr' }}>
        <BomSection />
        <MpsSection />
      </div>
      <MrpSection />
    </div>
  )
}

function BomSection() {
  const boms = useFetch('/ppic/boms')
  const products = useFetch('/master/products')
  const [open, setOpen] = useState(false)
  const [form, setForm] = useState({ product_id: '', output_qty: '1' })
  const [lines, setLines] = useState([{ material_id: '', qty_per_output: '', waste_factor: '0' }])
  const [msg, setMsg] = useState({ type: '', text: '' })

  const submit = async () => {
    setMsg({ type: 'error', text: '' })
    try {
      const res = await api('/ppic/boms/full', {
        method: 'POST',
        body: { product_id: Number(form.product_id), output_qty: Number(form.output_qty || 1), lines },
      })
      setMsg({ type: 'ok', text: `BOM ${res.code} dibuat (${res.line_count} baris).` })
      setOpen(false)
      boms.reload()
    } catch (e) {
      setMsg({ type: 'error', text: e.message })
    }
  }

  return (
    <div className="card">
      <h2>Bill of Materials (BOM)</h2>
      <table>
        <thead><tr><th>Kode</th><th>Produk</th><th>Output</th><th>Baris</th></tr></thead>
        <tbody>
          {(boms.data || []).map((b) => (
            <tr key={b.id}><td className="mono">{b.code}</td><td>{b.product_id}</td><td>{b.output_qty}</td><td>{b.line_count ?? '-'}</td></tr>
          ))}
          {!(boms.data || []).length && <tr><td colSpan={4} className="empty">Belum ada BOM.</td></tr>}
        </tbody>
      </table>

      {open && (
        <div style={{ marginTop: 14 }}>
          <div className="form-row">
            <div>
              <label>Produk Jadi (ID)</label>
              <select value={form.product_id} onChange={(e) => setForm({ ...form, product_id: e.target.value })}>
                <option value="">— pilih —</option>
                {(products.data || []).map((p) => <option key={p.id} value={p.id}>{p.code} · {p.name}</option>)}
              </select>
            </div>
            <div>
              <label>Output Qty</label>
              <input value={form.output_qty} onChange={(e) => setForm({ ...form, output_qty: e.target.value })} />
            </div>
          </div>
          <table>
            <thead><tr><th>Material</th><th>Qty/Output</th><th>Waste</th><th></th></tr></thead>
            <tbody>
              {lines.map((l, i) => (
                <tr key={i}>
                  <td>
                    <select value={l.material_id} onChange={(e) => setLines(lines.map((x, j) => (j === i ? { ...x, material_id: e.target.value } : x)))}>
                      <option value="">— pilih —</option>
                      {(products.data || []).map((p) => <option key={p.id} value={p.id}>{p.code}</option>)}
                    </select>
                  </td>
                  <td><input value={l.qty_per_output} onChange={(e) => setLines(lines.map((x, j) => (j === i ? { ...x, qty_per_output: e.target.value } : x)))} /></td>
                  <td><input value={l.waste_factor} onChange={(e) => setLines(lines.map((x, j) => (j === i ? { ...x, waste_factor: e.target.value } : x)))} /></td>
                  <td><button className="btn danger small" onClick={() => setLines(lines.filter((_, j) => j !== i))}>✕</button></td>
                </tr>
              ))}
            </tbody>
          </table>
          <div className="row-actions">
            <button className="btn ghost small" onClick={() => setLines([...lines, { material_id: '', qty_per_output: '', waste_factor: '0' }])}>+ Tambah Baris</button>
            <button className="btn" onClick={submit}>Simpan BOM</button>
          </div>
        </div>
      )}
      {!open && <button className="btn" style={{ marginTop: 12 }} onClick={() => setOpen(true)}>+ Buat BOM</button>}
      {msg.text && <div className={msg.type === 'ok' ? 'ok-msg' : 'error'}>{msg.text}</div>}
    </div>
  )
}

function MpsSection() {
  const mps = useFetch('/ppic/mps')
  const products = useFetch('/master/products')
  const [form, setForm] = useState({ product_id: '', qty: '', schedule_date: '', order_type: 'make_to_stock' })
  const [msg, setMsg] = useState('')

  const submit = async () => {
    setMsg('')
    try {
      const res = await api('/ppic/mps/full', {
        method: 'POST',
        body: {
          product_id: Number(form.product_id),
          qty: Number(form.qty),
          schedule_date: form.schedule_date || new Date().toISOString().slice(0, 10),
          order_type: form.order_type,
        },
      })
      setMsg(`MPS ${res.code} dibuat.`)
      mps.reload()
    } catch (e) { setMsg(e.message) }
  }

  return (
    <div className="card">
      <h2>Master Production Schedule (MPS)</h2>
      <div className="form-row">
        <div>
          <label>Produk</label>
          <select value={form.product_id} onChange={(e) => setForm({ ...form, product_id: e.target.value })}>
            <option value="">— pilih —</option>
            {(products.data || []).filter((p) => p.product_type === 'finished_good').map((p) => (
              <option key={p.id} value={p.id}>{p.code} · {p.name}</option>
            ))}
          </select>
        </div>
        <div>
          <label>Jumlah</label>
          <input value={form.qty} onChange={(e) => setForm({ ...form, qty: e.target.value })} />
        </div>
        <div>
          <label>Tanggal Jadwal</label>
          <input type="date" value={form.schedule_date} onChange={(e) => setForm({ ...form, schedule_date: e.target.value })} />
        </div>
        <div>
          <label>Tipe</label>
          <select value={form.order_type} onChange={(e) => setForm({ ...form, order_type: e.target.value })}>
            <option value="make_to_order">Make-to-Order</option>
            <option value="make_to_stock">Make-to-Stock</option>
          </select>
        </div>
      </div>
      <div className="row-actions"><button className="btn" onClick={submit}>Tambah MPS</button></div>
      {msg && <div className="ok-msg">{msg}</div>}

      <table style={{ marginTop: 16 }}>
        <thead><tr><th>Kode</th><th>Produk ID</th><th>Qty</th><th>Jadwal</th><th>Tipe</th><th>Status</th></tr></thead>
        <tbody>
          {(mps.data || []).map((m) => (
            <tr key={m.id}>
              <td className="mono">{m.code}</td>
              <td>{m.product_id}</td>
              <td>{m.qty}</td>
              <td>{m.schedule_date}</td>
              <td>{m.order_type}</td>
              <td><span className={`badge ${m.status}`}>{m.status}</span></td>
            </tr>
          ))}
          {!(mps.data || []).length && <tr><td colSpan={6} className="empty">Belum ada MPS.</td></tr>}
        </tbody>
      </table>
    </div>
  )
}

function MrpSection() {
  const mps = useFetch('/ppic/mps')
  const [mpsId, setMpsId] = useState('')
  const [result, setResult] = useState(null)
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)

  const run = async () => {
    if (!mpsId) return
    setBusy(true); setError(''); setResult(null)
    try {
      setResult(await api(`/ppic/mps/${mpsId}/mrp`))
    } catch (e) { setError(e.message) } finally { setBusy(false) }
  }

  return (
    <div className="card">
      <h2>Material Requirements Planning (MRP)</h2>
      <div className="form-row row3">
        <div>
          <label>Pilih MPS</label>
          <select value={mpsId} onChange={(e) => setMpsId(e.target.value)}>
            <option value="">— pilih MPS —</option>
            {(mps.data || []).map((m) => <option key={m.id} value={m.id}>{m.code} · produk {m.product_id}</option>)}
          </select>
        </div>
        <div style={{ alignSelf: 'end' }}><button className="btn" onClick={run} disabled={busy}>{busy ? 'Menghitung…' : 'Hitung MRP'}</button></div>
      </div>
      {error && <div className="error">{error}</div>}
      {result && (
        <div style={{ marginTop: 12 }}>
          <div className="muted">
            <b>{result.mps_code}</b> — Produk {result.product_code} · Kebutuhan {result.planned_qty} · BOM {result.bom_code}
          </div>
          <table style={{ marginTop: 10 }}>
            <thead><tr><th>Material</th><th>Kebutuhan Kotor</th><th>Stok</th><th>Kebutuhan Bersih</th><th>UoM</th></tr></thead>
            <tbody>
              {(result.requirements || []).map((r, i) => (
                <tr key={i}>
                  <td>{r.material_code} · {r.material_name}</td>
                  <td>{Number(r.gross_requirement).toLocaleString('id-ID')}</td>
                  <td>{Number(r.on_hand).toLocaleString('id-ID')}</td>
                  <td><b>{Number(r.net_requirement).toLocaleString('id-ID')}</b></td>
                  <td>{r.uom}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}