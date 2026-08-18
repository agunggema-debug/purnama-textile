import { useState } from 'react'
import { useFetch } from '../hooks.js'
import { api, fmtDate } from '../api.js'

export default function Warehouse() {
  return (
    <div>
      <h1>Modul Warehouse — Pergudangan &amp; Stok</h1>
      <InventorySection />
      <div className="grid" style={{ gridTemplateColumns: '1fr 1fr' }}>
        <GoodsReceiptSection />
        <MaterialIssueSection />
      </div>
      <div className="grid" style={{ gridTemplateColumns: '1fr 1fr' }}>
        <OpnameSection />
        <MovementsSection />
      </div>
    </div>
  )
}

function InventorySection() {
  const inv = useFetch('/warehouse/inventory')
  return (
    <div className="card">
      <h2>Inventory Tracking (Real-time)</h2>
      <table>
        <thead><tr><th>Kode</th><th>Produk</th><th>Lokasi</th><th>On-Hand</th><th>Reserved</th></tr></thead>
        <tbody>
          {(inv.data || []).map((i, idx) => (
            <tr key={idx}>
              <td className="mono">{i.product_code}</td>
              <td>{i.product_name}</td>
              <td>{i.location_code || '-'}</td>
              <td>{Number(i.on_hand).toLocaleString('id-ID')}</td>
              <td>{Number(i.reserved || 0).toLocaleString('id-ID')}</td>
            </tr>
          ))}
          {!(inv.data || []).length && <tr><td colSpan={5} className="empty">Belum ada data stok.</td></tr>}
        </tbody>
      </table>
    </div>
  )
}

function GoodsReceiptSection() {
  const gr = useFetch('/warehouse/goods-receipts')
  const po = useFetch('/purchasing/po')
  const products = useFetch('/master/products')
  const locations = useFetch('/master/locations')
  const [msg, setMsg] = useState('')
  const [poId, setPoId] = useState('')
  const [lines, setLines] = useState([{ product_id: '', location_id: '', qty: '', unit_cost: '' }])

  const submit = async () => {
    setMsg('')
    try {
      const res = await api('/warehouse/goods-receipts/full', {
        method: 'POST',
        body: {
          po_id: poId ? Number(poId) : null,
          receipt_date: new Date().toISOString().slice(0, 10),
          lines: lines.filter((l) => l.product_id && l.qty).map((l) => ({
            ...l,
            location_id: l.location_id ? Number(l.location_id) : null,
            qty: Number(l.qty), unit_cost: Number(l.unit_cost || 0),
          })),
        },
      })
      setMsg(`GR ${res.code} diposting, jurnal ${res.journal_id}.`); gr.reload(); setLines([{ product_id: '', location_id: '', qty: '', unit_cost: '' }])
    } catch (e) { setMsg(e.message) }
  }

  return (
    <div className="card">
      <h2>Goods Receipt &amp; Putaway</h2>
      <div className="form-row">
        <div>
          <label>PO Asal</label>
          <select value={poId} onChange={(e) => setPoId(e.target.value)}>
            <option value="">— tanpa PO —</option>
            {(po.data || []).map((p) => <option key={p.id} value={p.id}>{p.code}</option>)}
          </select>
        </div>
      </div>
      {lines.map((l, i) => (
        <div key={i} className="form-row row3">
          <select value={l.product_id} onChange={(e) => setLines(lines.map((x, j) => j === i ? { ...x, product_id: e.target.value } : x))}>
            <option value="">produk</option>
            {(products.data || []).map((p) => <option key={p.id} value={p.id}>{p.code}</option>)}
          </select>
          <select value={l.location_id} onChange={(e) => setLines(lines.map((x, j) => j === i ? { ...x, location_id: e.target.value } : x))}>
            <option value="">lokasi</option>
            {(locations.data || []).map((lc) => <option key={lc.id} value={lc.id}>{lc.code}</option>)}
          </select>
          <div className="row-actions" style={{ marginTop: 0 }}>
            <input value={l.qty} onChange={(e) => setLines(lines.map((x, j) => j === i ? { ...x, qty: e.target.value } : x))} placeholder="Qty" />
            <input value={l.unit_cost} onChange={(e) => setLines(lines.map((x, j) => j === i ? { ...x, unit_cost: e.target.value } : x))} placeholder="Harga" />
            <button className="btn danger small" onClick={() => setLines(lines.filter((_, j) => j !== i))}>✕</button>
          </div>
        </div>
      ))}
      <div className="row-actions">
        <button className="btn ghost small" onClick={() => setLines([...lines, { product_id: '', location_id: '', qty: '', unit_cost: '' }])}>+ Baris</button>
        <button className="btn" onClick={submit}>Terima Barang</button>
      </div>
      {msg && <div className="ok-msg">{msg}</div>}
      <table style={{ marginTop: 14 }}>
        <thead><tr><th>Kode</th><th>Tgl</th><th>Status</th></tr></thead>
        <tbody>
          {(gr.data || []).map((g) => <tr key={g.id}><td className="mono">{g.code}</td><td>{fmtDate(g.receipt_date)}</td><td>{g.status}</td></tr>)}
          {!(gr.data || []).length && <tr><td colSpan={3} className="empty">Belum ada penerimaan.</td></tr>}
        </tbody>
      </table>
    </div>
  )
}

function MaterialIssueSection() {
  const mi = useFetch('/warehouse/material-issues')
  const products = useFetch('/master/products')
  const locations = useFetch('/master/locations')
  const wo = useFetch('/production/work-orders')
  const [msg, setMsg] = useState('')
  const [woId, setWoId] = useState('')
  const [lines, setLines] = useState([{ product_id: '', location_id: '', qty: '' }])

  const submit = async () => {
    setMsg('')
    try {
      const res = await api('/warehouse/material-issues/full', {
        method: 'POST',
        body: {
          work_order_id: woId ? Number(woId) : null,
          issue_date: new Date().toISOString().slice(0, 10),
          lines: lines.filter((l) => l.product_id && l.qty).map((l) => ({
            ...l, location_id: l.location_id ? Number(l.location_id) : null, qty: Number(l.qty),
          })),
        },
      })
      setMsg(`MI ${res.code} diposting, jurnal ${res.journal_id}.`); mi.reload(); setLines([{ product_id: '', location_id: '', qty: '' }])
    } catch (e) { setMsg(e.message) }
  }

  return (
    <div className="card">
      <h2>Material Issue (ke Lantai Produksi)</h2>
      <div className="form-row">
        <div>
          <label>SPK (Work Order)</label>
          <select value={woId} onChange={(e) => setWoId(e.target.value)}>
            <option value="">— tanpa SPK —</option>
            {(wo.data || []).map((w) => <option key={w.id} value={w.id}>{w.code}</option>)}
          </select>
        </div>
      </div>
      {lines.map((l, i) => (
        <div key={i} className="form-row row3">
          <select value={l.product_id} onChange={(e) => setLines(lines.map((x, j) => j === i ? { ...x, product_id: e.target.value } : x))}>
            <option value="">produk</option>
            {(products.data || []).map((p) => <option key={p.id} value={p.id}>{p.code}</option>)}
          </select>
          <select value={l.location_id} onChange={(e) => setLines(lines.map((x, j) => j === i ? { ...x, location_id: e.target.value } : x))}>
            <option value="">lokasi</option>
            {(locations.data || []).map((lc) => <option key={lc.id} value={lc.id}>{lc.code}</option>)}
          </select>
          <div className="row-actions" style={{ marginTop: 0 }}>
            <input value={l.qty} onChange={(e) => setLines(lines.map((x, j) => j === i ? { ...x, qty: e.target.value } : x))} placeholder="Qty" />
            <button className="btn danger small" onClick={() => setLines(lines.filter((_, j) => j !== i))}>✕</button>
          </div>
        </div>
      ))}
      <div className="row-actions">
        <button className="btn ghost small" onClick={() => setLines([...lines, { product_id: '', location_id: '', qty: '' }])}>+ Baris</button>
        <button className="btn" onClick={submit}>Keluar Material</button>
      </div>
      {msg && <div className="ok-msg">{msg}</div>}
      <table style={{ marginTop: 14 }}>
        <thead><tr><th>Kode</th><th>Tgl</th><th>Status</th></tr></thead>
        <tbody>
          {(mi.data || []).map((m) => <tr key={m.id}><td className="mono">{m.code}</td><td>{fmtDate(m.issue_date)}</td><td>{m.status}</td></tr>)}
          {!(mi.data || []).length && <tr><td colSpan={3} className="empty">Belum ada pengeluaran material.</td></tr>}
        </tbody>
      </table>
    </div>
  )
}

function OpnameSection() {
  const op = useFetch('/warehouse/opnames')
  const products = useFetch('/master/products')
  const locations = useFetch('/master/locations')
  const [msg, setMsg] = useState('')
  const [lines, setLines] = useState([{ product_id: '', location_id: '', system_qty: '', actual_qty: '' }])

  const submit = async () => {
    setMsg('')
    try {
      const res = await api('/warehouse/opnames/full', {
        method: 'POST',
        body: {
          opname_date: new Date().toISOString().slice(0, 10),
          lines: lines.filter((l) => l.product_id).map((l) => ({
            ...l,
            location_id: l.location_id ? Number(l.location_id) : null,
            system_qty: Number(l.system_qty || 0), actual_qty: Number(l.actual_qty || 0),
          })),
        },
      })
      setMsg(`Opname ${res.code} selesai (${res.line_count} baris).`); op.reload(); setLines([{ product_id: '', location_id: '', system_qty: '', actual_qty: '' }])
    } catch (e) { setMsg(e.message) }
  }

  return (
    <div className="card">
      <h2>Stock Opname</h2>
      {lines.map((l, i) => (
        <div key={i} className="form-row">
          <div className="row3">
            <select value={l.product_id} onChange={(e) => setLines(lines.map((x, j) => j === i ? { ...x, product_id: e.target.value } : x))}>
              <option value="">produk</option>
              {(products.data || []).map((p) => <option key={p.id} value={p.id}>{p.code}</option>)}
            </select>
            <select value={l.location_id} onChange={(e) => setLines(lines.map((x, j) => j === i ? { ...x, location_id: e.target.value } : x))}>
              <option value="">lokasi</option>
              {(locations.data || []).map((lc) => <option key={lc.id} value={lc.id}>{lc.code}</option>)}
            </select>
            <div className="row-actions" style={{ marginTop: 0 }}>
              <input value={l.system_qty} onChange={(e) => setLines(lines.map((x, j) => j === i ? { ...x, system_qty: e.target.value } : x))} placeholder="Sistem" />
              <input value={l.actual_qty} onChange={(e) => setLines(lines.map((x, j) => j === i ? { ...x, actual_qty: e.target.value } : x))} placeholder="Fisik" />
              <button className="btn danger small" onClick={() => setLines(lines.filter((_, j) => j !== i))}>✕</button>
            </div>
          </div>
        </div>
      ))}
      <div className="row-actions">
        <button className="btn ghost small" onClick={() => setLines([...lines, { product_id: '', location_id: '', system_qty: '', actual_qty: '' }])}>+ Baris</button>
        <button className="btn" onClick={submit}>Selesaikan Opname</button>
      </div>
      {msg && <div className="ok-msg">{msg}</div>}
      <table style={{ marginTop: 14 }}>
        <thead><tr><th>Kode</th><th>Tgl</th><th>Status</th></tr></thead>
        <tbody>
          {(op.data || []).map((o) => <tr key={o.id}><td className="mono">{o.code}</td><td>{fmtDate(o.opname_date)}</td><td>{o.status}</td></tr>)}
          {!(op.data || []).length && <tr><td colSpan={3} className="empty">Belum ada opname.</td></tr>}
        </tbody>
      </table>
    </div>
  )
}

function MovementsSection() {
  const mv = useFetch('/warehouse/movements')
  return (
    <div className="card">
      <h2>Buku Besar Stok (Movements)</h2>
      <table>
        <thead><tr><th>Tanggal</th><th>Produk</th><th>Tipe</th><th>Masuk/Keluar</th><th>Qty</th></tr></thead>
        <tbody>
          {(mv.data || []).map((t) => (
            <tr key={t.id}>
              <td>{fmtDate(t.transaction_date)}</td>
              <td>{t.product_code}</td>
              <td><span className={`badge ${t.direction === 'in' ? 'ok' : 'rejected'}`}>{t.movement_type}</span></td>
              <td>{t.direction === 'in' ? 'Masuk' : 'Keluar'}</td>
              <td>{Number(t.qty).toLocaleString('id-ID')}</td>
            </tr>
          ))}
          {!(mv.data || []).length && <tr><td colSpan={5} className="empty">Belum ada pergerakan stok.</td></tr>}
        </tbody>
      </table>
    </div>
  )
}