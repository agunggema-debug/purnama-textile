import { useState } from 'react'
import { useFetch } from '../hooks.js'
import { api, fmtDate } from '../api.js'

const badge = (s) => <span className={`badge ${s}`}>{s}</span>

export default function Distribution() {
  return (
    <div>
      <h1>Modul Distribusi &amp; Logistik</h1>
      <div className="grid" style={{ gridTemplateColumns: '1fr 1fr' }}>
        <SalesOrderSection />
        <DeliveryOrderSection />
      </div>
      <PackingSection />
    </div>
  )
}

function SalesOrderSection() {
  const so = useFetch('/distribution/sales-orders')
  const customers = useFetch('/master/customers')
  const products = useFetch('/master/products')
  const [msg, setMsg] = useState('')
  const [customerId, setCustomerId] = useState('')
  const [lines, setLines] = useState([{ product_id: '', qty: '', unit_price: '', delivery_date: '' }])

  const setLine = (i, patch) => setLines(lines.map((x, j) => (j === i ? { ...x, ...patch } : x)))

  const submit = async () => {
    setMsg('')
    try {
      const today = new Date().toISOString().slice(0, 10)
      const res = await api('/distribution/sales-orders/full', {
        method: 'POST',
        body: {
          customer_id: customerId ? Number(customerId) : null,
          order_date: today,
          lines: lines.filter((l) => l.product_id && l.qty).map((l) => ({
            ...l,
            product_id: Number(l.product_id), qty: Number(l.qty),
            unit_price: Number(l.unit_price || 0), delivery_date: l.delivery_date || today,
          })),
        },
      })
      setMsg(`SO ${res.code} dibuat (${res.line_count} baris).`); so.reload()
    } catch (e) { setMsg(e.message) }
  }

  return (
    <div className="card">
      <h2>Sales Order (B2B/B2C)</h2>
      <div className="form-row">
        <div>
          <label>Customer</label>
          <select value={customerId} onChange={(e) => setCustomerId(e.target.value)}>
            <option value="">— pilih customer —</option>
            {(customers.data || []).map((c) => <option key={c.id} value={c.id}>{c.name}</option>)}
          </select>
        </div>
      </div>
      <table>
        <thead><tr><th>Produk</th><th>Qty</th><th>Harga</th><th>Tgl Kirim</th><th></th></tr></thead>
        <tbody>
          {lines.map((l, i) => (
            <tr key={i}>
              <td>
                <select value={l.product_id} onChange={(e) => setLine(i, { product_id: e.target.value })}>
                  <option value="">— pilih —</option>
                  {(products.data || []).filter((p) => p.product_type === 'finished_good').map((p) => (
                    <option key={p.id} value={p.id}>{p.code}</option>
                  ))}
                </select>
              </td>
              <td><input value={l.qty} onChange={(e) => setLine(i, { qty: e.target.value })} /></td>
              <td><input value={l.unit_price} onChange={(e) => setLine(i, { unit_price: e.target.value })} /></td>
              <td><input type="date" value={l.delivery_date} onChange={(e) => setLine(i, { delivery_date: e.target.value })} /></td>
              <td><button className="btn danger small" onClick={() => setLines(lines.filter((_, j) => j !== i))}>✕</button></td>
            </tr>
          ))}
        </tbody>
      </table>
      <div className="row-actions">
        <button className="btn ghost small" onClick={() => setLines([...lines, { product_id: '', qty: '', unit_price: '', delivery_date: '' }])}>+ Baris</button>
        <button className="btn" onClick={submit}>Buat SO</button>
      </div>
      {msg && <div className="ok-msg">{msg}</div>}
    </div>
  )
}

function DeliveryOrderSection() {
  const doList = useFetch('/distribution/delivery-orders')
  const so = useFetch('/distribution/sales-orders')
  const products = useFetch('/master/products')
  const locations = useFetch('/master/locations')
  const [msg, setMsg] = useState('')
  const [soId, setSoId] = useState('')
  const [lines, setLines] = useState([{ product_id: '', location_id: '', qty: '' }])

  const setLine = (i, patch) => setLines(lines.map((x, j) => (j === i ? { ...x, ...patch } : x)))

  const submit = async () => {
    setMsg('')
    try {
      const res = await api('/distribution/delivery-orders/full', {
        method: 'POST',
        body: {
          sales_order_id: soId ? Number(soId) : null,
          delivery_date: new Date().toISOString().slice(0, 10),
          lines: lines.filter((l) => l.product_id && l.qty).map((l) => ({
            ...l,
            product_id: Number(l.product_id),
            location_id: l.location_id ? Number(l.location_id) : null,
            qty: Number(l.qty),
          })),
        },
      })
      setMsg(`DO ${res.code} diposting — Pendapatan ${res.revenue}, HPP ${res.cogs}.`)
      doList.reload()
    } catch (e) { setMsg(e.message) }
  }

  return (
    <div className="card">
      <h2>Delivery Order &amp; Surat Jalan</h2>
      <div className="form-row">
        <div>
          <label>SO Asal</label>
          <select value={soId} onChange={(e) => setSoId(e.target.value)}>
            <option value="">— tanpa SO —</option>
            {(so.data || []).map((s) => <option key={s.id} value={s.id}>{s.code}</option>)}
          </select>
        </div>
      </div>
      {lines.map((l, i) => (
        <div key={i} className="form-row row3">
          <select value={l.product_id} onChange={(e) => setLine(i, { product_id: e.target.value })}>
            <option value="">produk</option>
            {(products.data || []).map((p) => <option key={p.id} value={p.id}>{p.code}</option>)}
          </select>
          <select value={l.location_id} onChange={(e) => setLine(i, { location_id: e.target.value })}>
            <option value="">lokasi</option>
            {(locations.data || []).map((lc) => <option key={lc.id} value={lc.id}>{lc.code}</option>)}
          </select>
          <div className="row-actions" style={{ marginTop: 0 }}>
            <input value={l.qty} onChange={(e) => setLine(i, { qty: e.target.value })} placeholder="Qty" />
            <button className="btn danger small" onClick={() => setLines(lines.filter((_, j) => j !== i))}>✕</button>
          </div>
        </div>
      ))}
      <div className="row-actions">
        <button className="btn ghost small" onClick={() => setLines([...lines, { product_id: '', location_id: '', qty: '' }])}>+ Baris</button>
        <button className="btn" onClick={submit}>Terbitkan DO</button>
      </div>
      {msg && <div className="ok-msg">{msg}</div>}

      <table style={{ marginTop: 14 }}>
        <thead><tr><th>Kode</th><th>Tgl</th><th>Status</th></tr></thead>
        <tbody>
          {(doList.data || []).map((d) => <tr key={d.id}><td className="mono">{d.code}</td><td>{fmtDate(d.delivery_date)}</td><td>{badge(d.status)}</td></tr>)}
          {!(doList.data || []).length && <tr><td colSpan={3} className="empty">Belum ada DO.</td></tr>}
        </tbody>
      </table>
    </div>
  )
}

function PackingSection() {
  const pl = useFetch('/distribution/packing-lists')
  const doList = useFetch('/distribution/delivery-orders')
  const products = useFetch('/master/products')
  const [msg, setMsg] = useState('')
  const [doId, setDoId] = useState('')
  const [packages, setPackages] = useState('')
  const [lines, setLines] = useState([{ product_id: '', qty: '' }])

  const setLine = (i, patch) => setLines(lines.map((x, j) => (j === i ? { ...x, ...patch } : x)))

  const submit = async () => {
    setMsg('')
    try {
      const res = await api('/distribution/packing-lists/full', {
        method: 'POST',
        body: {
          delivery_order_id: Number(doId),
          total_packages: Number(packages || 0),
          lines: lines.filter((l) => l.product_id && l.qty).map((l) => ({ ...l, product_id: Number(l.product_id), qty: Number(l.qty) })),
        },
      })
      setMsg(`Packing List ${res.code} dibuat.`); pl.reload()
    } catch (e) { setMsg(e.message) }
  }

  return (
    <div className="card">
      <h2>Packing List</h2>
      <div className="form-row row3">
        <div>
          <label>DO</label>
          <select value={doId} onChange={(e) => setDoId(e.target.value)}>
            <option value="">— pilih DO —</option>
            {(doList.data || []).map((d) => <option key={d.id} value={d.id}>{d.code}</option>)}
          </select>
        </div>
        <div>
          <label>Total Kemasan</label>
          <input value={packages} onChange={(e) => setPackages(e.target.value)} />
        </div>
      </div>
      {lines.map((l, i) => (
        <div key={i} className="form-row row3">
          <select value={l.product_id} onChange={(e) => setLine(i, { product_id: e.target.value })}>
            <option value="">produk</option>
            {(products.data || []).map((p) => <option key={p.id} value={p.id}>{p.code}</option>)}
          </select>
          <input value={l.qty} onChange={(e) => setLine(i, { qty: e.target.value })} placeholder="Qty" />
          <button className="btn danger small" onClick={() => setLines(lines.filter((_, j) => j !== i))}>✕</button>
        </div>
      ))}
      <div className="row-actions">
        <button className="btn ghost small" onClick={() => setLines([...lines, { product_id: '', qty: '' }])}>+ Baris</button>
        <button className="btn" onClick={submit}>Buat Packing List</button>
      </div>
      {msg && <div className="ok-msg">{msg}</div>}
    </div>
  )
}