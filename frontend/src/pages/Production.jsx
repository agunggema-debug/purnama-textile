import { useState } from 'react'
import { useFetch } from '../hooks.js'
import { api } from '../api.js'

const badge = (s) => <span className={`badge ${s}`}>{s}</span>

export default function Production() {
  return (
    <div>
      <h1>Modul Produksi — Manufaktur &amp; Tracking</h1>
      <div className="grid" style={{ gridTemplateColumns: '1.2fr 1fr' }}>
        <WorkOrderSection />
        <QcSection />
      </div>
      <WorkOrderList />
    </div>
  )
}

function WorkOrderSection() {
  const wo = useFetch('/production/work-orders')
  const mps = useFetch('/ppic/mps')
  const products = useFetch('/master/products')
  const wc = useFetch('/master/workcenters')
  const [msg, setMsg] = useState('')
  const [form, setForm] = useState({ mps_id: '', product_id: '', planned_qty: '', start_date: '', due_date: '' })
  const [wcs, setWcs] = useState([])

  const toggleWc = (id) =>
    setWcs((prev) => (prev.includes(id) ? prev.filter((x) => x !== id) : [...prev, id]))

  const submit = async () => {
    setMsg('')
    try {
      const res = await api('/production/work-orders/full', {
        method: 'POST',
        body: {
          mps_id: form.mps_id ? Number(form.mps_id) : null,
          product_id: Number(form.product_id),
          planned_qty: Number(form.planned_qty),
          start_date: form.start_date || new Date().toISOString().slice(0, 10),
          due_date: form.due_date || new Date().toISOString().slice(0, 10),
          workcenter_ids: wcs,
        },
      })
      setMsg(`SPK ${res.code} dibuat dengan ${res.operations} operasi routing.`); wo.reload()
    } catch (e) { setMsg(e.message) }
  }

  return (
    <div className="card">
      <h2>Surat Perintah Kerja (SPK)</h2>
      <div className="form-row">
        <div>
          <label>Produk Jadi</label>
          <select value={form.product_id} onChange={(e) => setForm({ ...form, product_id: e.target.value })}>
            <option value="">— pilih —</option>
            {(products.data || []).filter((p) => p.product_type === 'finished_good').map((p) => (
              <option key={p.id} value={p.id}>{p.code} · {p.name}</option>
            ))}
          </select>
        </div>
        <div>
          <label>Jumlah Rencana</label>
          <input value={form.planned_qty} onChange={(e) => setForm({ ...form, planned_qty: e.target.value })} />
        </div>
        <div>
          <label>Mulai</label>
          <input type="date" value={form.start_date} onChange={(e) => setForm({ ...form, start_date: e.target.value })} />
        </div>
        <div>
          <label>Selesai</label>
          <input type="date" value={form.due_date} onChange={(e) => setForm({ ...form, due_date: e.target.value })} />
        </div>
        <div>
          <label>Dari MPS (opsional)</label>
          <select value={form.mps_id} onChange={(e) => setForm({ ...form, mps_id: e.target.value })}>
            <option value="">— tanpa MPS —</option>
            {(mps.data || []).map((m) => <option key={m.id} value={m.id}>{m.code}</option>)}
          </select>
        </div>
      </div>
      <div className="muted" style={{ marginBottom: 8 }}>Routing (pilih stasiun kerja)</div>
      <div className="row-actions" style={{ flexWrap: 'wrap' }}>
        {(wc.data || []).map((c) => (
          <button key={c.id}
            className={`btn small ${wcs.includes(c.id) ? '' : 'ghost'}`}
            onClick={() => toggleWc(c.id)}>
            {c.code} · {c.name}
          </button>
        ))}
      </div>
      <div className="row-actions"><button className="btn" onClick={submit}>Terbitkan SPK</button></div>
      {msg && <div className="ok-msg">{msg}</div>}
    </div>
  )
}

function QcSection() {
  const products = useFetch('/master/products')
  const wo = useFetch('/production/work-orders')
  const [msg, setMsg] = useState('')
  const [form, setForm] = useState({ work_order_id: '', product_id: '', inspected_qty: '', passed_qty: '', rejected_qty: '', decision: 'pass' })

  const submit = async () => {
    setMsg('')
    try {
      const res = await api('/production/qc/full', {
        method: 'POST',
        body: {
          work_order_id: form.work_order_id ? Number(form.work_order_id) : null,
          product_id: Number(form.product_id),
          inspected_qty: Number(form.inspected_qty),
          passed_qty: Number(form.passed_qty),
          rejected_qty: Number(form.rejected_qty),
          decision: form.decision,
        },
      })
      setMsg(`QC dicatat, keputusan: ${res.decision}.`)
    } catch (e) { setMsg(e.message) }
  }

  return (
    <div className="card">
      <h2>Quality Control (QC)</h2>
      <div className="form-row">
        <div>
          <label>Produk</label>
          <select value={form.product_id} onChange={(e) => setForm({ ...form, product_id: e.target.value })}>
            <option value="">— pilih —</option>
            {(products.data || []).map((p) => <option key={p.id} value={p.id}>{p.code}</option>)}
          </select>
        </div>
        <div>
          <label>SPK</label>
          <select value={form.work_order_id} onChange={(e) => setForm({ ...form, work_order_id: e.target.value })}>
            <option value="">— tanpa SPK —</option>
            {(wo.data || []).map((w) => <option key={w.id} value={w.id}>{w.code}</option>)}
          </select>
        </div>
      </div>
      <div className="form-row row3">
        <div><label>Diinspeksi</label><input value={form.inspected_qty} onChange={(e) => setForm({ ...form, inspected_qty: e.target.value })} /></div>
        <div><label>Lolos</label><input value={form.passed_qty} onChange={(e) => setForm({ ...form, passed_qty: e.target.value })} /></div>
        <div><label>Reject</label><input value={form.rejected_qty} onChange={(e) => setForm({ ...form, rejected_qty: e.target.value })} /></div>
      </div>
      <div className="form-row">
        <div>
          <label>Keputusan</label>
          <select value={form.decision} onChange={(e) => setForm({ ...form, decision: e.target.value })}>
            <option value="pass">Lolos (Pass)</option>
            <option value="rework">Rework</option>
            <option value="reject">Reject</option>
          </select>
        </div>
      </div>
      <button className="btn" onClick={submit}>Simpan Hasil QC</button>
      {msg && <div className="ok-msg">{msg}</div>}
    </div>
  )
}

function WorkOrderList() {
  const wo = useFetch('/production/work-orders')
  const [detail, setDetail] = useState(null)

  const openDetail = async (id) => setDetail(await api(`/production/work-orders/${id}/detail`))

  const advance = async (woId, opId) => {
    await api(`/production/work-orders/${woId}/operations/${opId}/update`, {
      method: 'POST',
      body: { status: 'completed' },
    })
    setDetail(await api(`/production/work-orders/${woId}/detail`))
  }

  return (
    <div className="card">
      <h2>Daftar SPK &amp; Workcenter Routing</h2>
      <table>
        <thead><tr><th>Kode</th><th>Produk</th><th>Rencana</th><th>Diproduksi</th><th>Status</th><th></th></tr></thead>
        <tbody>
          {(wo.data || []).map((w) => (
            <tr key={w.id}>
              <td className="mono">{w.code}</td>
              <td>{w.product_id}</td>
              <td>{w.planned_qty}</td>
              <td>{w.produced_qty || 0}</td>
              <td>{badge(w.status)}</td>
              <td><button className="btn ghost small" onClick={() => openDetail(w.id)}>Routing</button></td>
            </tr>
          ))}
          {!(wo.data || []).length && <tr><td colSpan={6} className="empty">Belum ada SPK.</td></tr>}
        </tbody>
      </table>

      {detail && (
        <div style={{ marginTop: 16 }}>
          <h3 style={{ marginBottom: 8 }}>Routing — {detail.code} ({detail.product_name})</h3>
          <table>
            <thead><tr><th>Urutan</th><th>Workcenter</th><th>Status</th><th>Selesai</th><th>Reject</th><th></th></tr></thead>
            <tbody>
              {(detail.operations || []).map((o) => (
                <tr key={o.id}>
                  <td>{o.sequence}</td>
                  <td>{o.workcenter} <span className="muted">({o.workcenter_type})</span></td>
                  <td>{badge(o.status)}</td>
                  <td>{o.qty_completed}</td>
                  <td>{o.qty_rejected}</td>
                  <td>{o.status !== 'completed' && <button className="btn ok small" onClick={() => advance(detail.id, o.id)}>Selesaikan</button>}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}