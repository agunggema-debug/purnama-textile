import { useState } from 'react'
import { useFetch } from '../hooks.js'
import { api } from '../api.js'

const badge = (s) => <span className={`badge ${s}`}>{s}</span>

export default function Purchasing() {
  return (
    <div>
      <h1>Modul Purchasing — Pengadaan Bahan Baku</h1>
      <div className="grid" style={{ gridTemplateColumns: '1fr 1fr' }}>
        <PRSection />
        <PoSection />
      </div>
      <ReturnSection />
    </div>
  )
}

function PRSection() {
  const pr = useFetch('/purchasing/pr')
  const products = useFetch('/master/products')
  const [msg, setMsg] = useState('')
  const [lines, setLines] = useState([{ product_id: '', qty: '' }])

  const submit = async () => {
    setMsg('')
    try {
      const res = await api('/purchasing/pr/full', {
        method: 'POST',
        body: {
          requested_by: 'PPIC',
          requested_date: new Date().toISOString().slice(0, 10),
          lines: lines.filter((l) => l.product_id && l.qty),
        },
      })
      setMsg(`PR ${res.code} dibuat.`); pr.reload(); setLines([{ product_id: '', qty: '' }])
    } catch (e) { setMsg(e.message) }
  }

  const approve = async (id) => { await api(`/purchasing/pr/${id}/approve`, { method: 'POST' }); pr.reload() }

  return (
    <div className="card">
      <h2>Purchase Request (PR)</h2>
      <table>
        <thead><tr><th>Kode</th><th>Diminta oleh</th><th>Status</th><th></th></tr></thead>
        <tbody>
          {(pr.data || []).map((r) => (
            <tr key={r.id}>
              <td className="mono">{r.code}</td><td>{r.requested_by}</td>
              <td>{badge(r.status)}</td>
              <td>{r.status === 'draft' && <button className="btn ok small" onClick={() => approve(r.id)}>Setujui</button>}</td>
            </tr>
          ))}
          {!(pr.data || []).length && <tr><td colSpan={4} className="empty">Belum ada PR.</td></tr>}
        </tbody>
      </table>
      <div style={{ marginTop: 12 }}>
        <table>
          <thead><tr><th>Material</th><th>Qty</th><th></th></tr></thead>
          <tbody>
            {lines.map((l, i) => (
              <tr key={i}>
                <td>
                  <select value={l.product_id} onChange={(e) => setLines(lines.map((x, j) => j === i ? { ...x, product_id: e.target.value } : x))}>
                    <option value="">— pilih —</option>
                    {(products.data || []).map((p) => <option key={p.id} value={p.id}>{p.code}</option>)}
                  </select>
                </td>
                <td><input value={l.qty} onChange={(e) => setLines(lines.map((x, j) => j === i ? { ...x, qty: e.target.value } : x))} /></td>
                <td><button className="btn danger small" onClick={() => setLines(lines.filter((_, j) => j !== i))}>✕</button></td>
              </tr>
            ))}
          </tbody>
        </table>
        <div className="row-actions">
          <button className="btn ghost small" onClick={() => setLines([...lines, { product_id: '', qty: '' }])}>+ Baris</button>
          <button className="btn" onClick={submit}>Buat PR</button>
        </div>
        {msg && <div className="ok-msg">{msg}</div>}
      </div>
    </div>
  )
}

function PoSection() {
  const po = useFetch('/purchasing/po')
  const vendors = useFetch('/master/vendors')
  const products = useFetch('/master/products')
  const [msg, setMsg] = useState('')
  const [vendorId, setVendorId] = useState('')
  const [lines, setLines] = useState([{ product_id: '', qty: '', unit_price: '' }])

  const submit = async () => {
    setMsg('')
    try {
      const res = await api('/purchasing/po/full', {
        method: 'POST',
        body: {
          vendor_id: Number(vendorId),
          order_date: new Date().toISOString().slice(0, 10),
          lines: lines.filter((l) => l.product_id && l.qty),
        },
      })
      setMsg(`PO ${res.code} dibuat.`); po.reload(); setLines([{ product_id: '', qty: '', unit_price: '' }])
    } catch (e) { setMsg(e.message) }
  }

  const approve = async (id) => { await api(`/purchasing/po/${id}/approve`, { method: 'POST' }); po.reload() }

  return (
    <div className="card">
      <h2>Purchase Order (PO)</h2>
      <div className="form-row">
        <div>
          <label>Vendor</label>
          <select value={vendorId} onChange={(e) => setVendorId(e.target.value)}>
            <option value="">— pilih vendor —</option>
            {(vendors.data || []).map((v) => <option key={v.id} value={v.id}>{v.name}</option>)}
          </select>
        </div>
      </div>
      <table>
        <thead><tr><th>Material</th><th>Qty</th><th>Harga</th><th></th></tr></thead>
        <tbody>
          {lines.map((l, i) => (
            <tr key={i}>
              <td>
                <select value={l.product_id} onChange={(e) => setLines(lines.map((x, j) => j === i ? { ...x, product_id: e.target.value } : x))}>
                  <option value="">— pilih —</option>
                  {(products.data || []).map((p) => <option key={p.id} value={p.id}>{p.code}</option>)}
                </select>
              </td>
              <td><input value={l.qty} onChange={(e) => setLines(lines.map((x, j) => j === i ? { ...x, qty: e.target.value } : x))} /></td>
              <td><input value={l.unit_price} onChange={(e) => setLines(lines.map((x, j) => j === i ? { ...x, unit_price: e.target.value } : x))} /></td>
              <td><button className="btn danger small" onClick={() => setLines(lines.filter((_, j) => j !== i))}>✕</button></td>
            </tr>
          ))}
        </tbody>
      </table>
      <div className="row-actions">
        <button className="btn ghost small" onClick={() => setLines([...lines, { product_id: '', qty: '', unit_price: '' }])}>+ Baris</button>
        <button className="btn" onClick={submit}>Buat PO</button>
      </div>
      {msg && <div className="ok-msg">{msg}</div>}

      <table style={{ marginTop: 16 }}>
        <thead><tr><th>Kode</th><th>Vendor</th><th>Tgl</th><th>ETA</th><th>Status</th><th></th></tr></thead>
        <tbody>
          {(po.data || []).map((p) => (
            <tr key={p.id}>
              <td className="mono">{p.code}</td>
              <td>{p.vendor_id}</td>
              <td>{p.order_date}</td>
              <td>{p.expected_arrival || '-'}</td>
              <td>{badge(p.status)}</td>
              <td>{p.status === 'draft' && <button className="btn ok small" onClick={() => approve(p.id)}>Setujui</button>}</td>
            </tr>
          ))}
          {!(po.data || []).length && <tr><td colSpan={6} className="empty">Belum ada PO.</td></tr>}
        </tbody>
      </table>
    </div>
  )
}

function ReturnSection() {
  const returns = useFetch('/purchasing/returns')
  const po = useFetch('/purchasing/po')
  const products = useFetch('/master/products')
  const [msg, setMsg] = useState('')
  const [poId, setPoId] = useState('')
  const [lines, setLines] = useState([{ product_id: '', qty: '' }])

  const submit = async () => {
    setMsg('')
    try {
      const res = await api('/purchasing/returns/full', {
        method: 'POST',
        body: { po_id: Number(poId), lines: lines.filter((l) => l.product_id && l.qty) },
      })
      setMsg(`Retur ${res.code} dibuat.`); returns.reload(); setPoId(''); setLines([{ product_id: '', qty: '' }])
    } catch (e) { setMsg(e.message) }
  }

  return (
    <div className="card">
      <h2>Retur Pembelian</h2>
      <div className="form-row">
        <div>
          <label>PO Asal</label>
          <select value={poId} onChange={(e) => setPoId(e.target.value)}>
            <option value="">— pilih PO —</option>
            {(po.data || []).map((p) => <option key={p.id} value={p.id}>{p.code}</option>)}
          </select>
        </div>
      </div>
      <div className="form-row">
        {lines.map((l, i) => (
          <div key={i} className="row2">
            <select value={l.product_id} onChange={(e) => setLines(lines.map((x, j) => j === i ? { ...x, product_id: e.target.value } : x))}>
              <option value="">material</option>
              {(products.data || []).map((p) => <option key={p.id} value={p.id}>{p.code}</option>)}
            </select>
            <div className="row-actions" style={{ marginTop: 0 }}>
              <input value={l.qty} onChange={(e) => setLines(lines.map((x, j) => j === i ? { ...x, qty: e.target.value } : x))} placeholder="Qty" />
              <button className="btn danger small" onClick={() => setLines(lines.filter((_, j) => j !== i))}>✕</button>
            </div>
          </div>
        ))}
      </div>
      <div className="row-actions">
        <button className="btn ghost small" onClick={() => setLines([...lines, { product_id: '', qty: '' }])}>+ Baris</button>
        <button className="btn" onClick={submit}>Catat Retur</button>
      </div>
      {msg && <div className="ok-msg">{msg}</div>}

      <table style={{ marginTop: 16 }}>
        <thead><tr><th>Kode</th><th>PO</th><th>Tanggal</th><th>Status</th></tr></thead>
        <tbody>
          {(returns.data || []).map((r) => (
            <tr key={r.id}><td className="mono">{r.code}</td><td>{r.po_id}</td><td>{r.return_date}</td><td>{badge(r.status)}</td></tr>
          ))}
          {!(returns.data || []).length && <tr><td colSpan={4} className="empty">Belum ada retur.</td></tr>}
        </tbody>
      </table>
    </div>
  )
}