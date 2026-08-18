import { useState } from 'react'
import { useFetch } from '../hooks.js'
import { api, fmtIDR, fmtDate } from '../api.js'

export default function Finance() {
  const pl = useFetch('/finance/reports/profit-loss')
  const bs = useFetch('/finance/reports/balance-sheet')
  const cf = useFetch('/finance/reports/cash-flow')
  const ap = useFetch('/finance/ap/overview')
  const ar = useFetch('/finance/ar/overview')

  const pnl = pl.data || {}
  const bal = bs.data || {}
  const flow = cf.data || {}

  return (
    <div>
      <h1>Finance &amp; Accounting</h1>

      <div className="cards">
        <div className="stat-card"><div className="label">Pendapatan</div><div className="value">{fmtIDR(pnl.revenue)}</div></div>
        <div className="stat-card"><div className="label">Beban</div><div className="value">{fmtIDR(pnl.expense)}</div></div>
        <div className="stat-card"><div className="label">Laba Bersih (P&amp;L)</div><div className="value">{fmtIDR(pnl.net_profit)}</div></div>
        <div className="stat-card"><div className="label">Total Aset</div><div className="value">{fmtIDR(bal.assets)}</div></div>
        <div className="stat-card"><div className="label">Arus Kas Bersih</div><div className="value">{fmtIDR(flow.net_cash_flow)}</div></div>
      </div>

      <div className="grid" style={{ gridTemplateColumns: '1fr 1fr' }}>
        <ApArSection ap={ap} ar={ar} />
        <PaymentsSection />
      </div>
      <PayrollSection />
      <JournalSection />
    </div>
  )
}

function ApArSection({ ap, ar }) {
  return (
    <div className="card">
      <h2>Hutang (AP) &amp; Piutang (AR)</h2>
      <h3 style={{ fontSize: 13, margin: '8px 0' }}>Hutang kepada Vendor</h3>
      <table>
        <thead><tr><th>Kode</th><th>Vendor</th><th>Jatuh Tempo</th><th>Saldo</th></tr></thead>
        <tbody>
          {(ap.data || []).map((i) => (
            <tr key={i.id}><td className="mono">{i.code}</td><td>{i.vendor}</td><td>{fmtDate(i.due_date)}</td><td>{fmtIDR(i.balance)}</td></tr>
          ))}
          {!(ap.data || []).length && <tr><td colSpan={4} className="empty">Belum ada hutang.</td></tr>}
        </tbody>
      </table>
      <h3 style={{ fontSize: 13, margin: '8px 0' }}>Piutang dari Pelanggan</h3>
      <table>
        <thead><tr><th>Kode</th><th>Customer</th><th>Jatuh Tempo</th><th>Saldo</th></tr></thead>
        <tbody>
          {(ar.data || []).map((i) => (
            <tr key={i.id}><td className="mono">{i.code}</td><td>{i.customer}</td><td>{fmtDate(i.due_date)}</td><td>{fmtIDR(i.balance)}</td></tr>
          ))}
          {!(ar.data || []).length && <tr><td colSpan={4} className="empty">Belum ada piutang.</td></tr>}
        </tbody>
      </table>
    </div>
  )
}

function PaymentsSection() {
  const [msg, setMsg] = useState('')
  return (
    <div className="card">
      <h2>Pencatatan Pembayaran</h2>
      <div className="row3" style={{ gap: 14 }}>
        <PaymentInForm setMsg={setMsg} />
        <PaymentOutForm setMsg={setMsg} />
      </div>
      {msg && <div className="ok-msg">{msg}</div>}
    </div>
  )
}

function PaymentInForm({ setMsg }) {
  const ar = useFetch('/finance/ar')
  const [invId, setInvId] = useState('')
  const [amount, setAmount] = useState('')

  const submit = async () => {
    setMsg('')
    try {
      const res = await api('/finance/payments-in/full', {
        method: 'POST',
        body: { ar_invoice_id: Number(invId), amount: Number(amount), method: 'transfer' },
      })
      if (res.error) { setMsg('Periksa kembali invoice.'); return }
      setMsg(`Pembayaran AR ${res.ar_invoice} dicatat. Saldo: ${res.balance}.`)
    } catch (e) { setMsg(e.message) }
  }
  return (
    <div>
      <label>Terima dari AR invoice</label>
      <select value={invId} onChange={(e) => setInvId(e.target.value)}>
        <option value="">— pilih AR —</option>
        {(ar.data || []).map((i) => <option key={i.id} value={i.id}>{i.code}</option>)}
      </select>
      <label>Jumlah</label>
      <input value={amount} onChange={(e) => setAmount(e.target.value)} />
      <button className="btn ok small" style={{ marginTop: 6 }} onClick={submit}>Catat Penerimaan</button>
    </div>
  )
}

function PaymentOutForm({ setMsg }) {
  const ap = useFetch('/finance/ap')
  const [invId, setInvId] = useState('')
  const [amount, setAmount] = useState('')

  const submit = async () => {
    setMsg('')
    try {
      const res = await api('/finance/payments-out/full', {
        method: 'POST',
        body: { ap_invoice_id: Number(invId), amount: Number(amount), method: 'transfer' },
      })
      if (res.error) { setMsg('Periksa kembali invoice.'); return }
      setMsg(`Pembayaran AP ${res.ap_invoice} dicatat. Saldo: ${res.balance}.`)
    } catch (e) { setMsg(e.message) }
  }
  return (
    <div>
      <label>Bayar ke AP invoice</label>
      <select value={invId} onChange={(e) => setInvId(e.target.value)}>
        <option value="">— pilih AP —</option>
        {(ap.data || []).map((i) => <option key={i.id} value={i.id}>{i.code}</option>)}
      </select>
      <label>Jumlah</label>
      <input value={amount} onChange={(e) => setAmount(e.target.value)} />
      <button className="btn small" style={{ marginTop: 6 }} onClick={submit}>Catat Pembayaran</button>
    </div>
  )
}

function PayrollSection() {
  const runs = useFetch('/finance/payroll-runs')
  const [msg, setMsg] = useState('')
  const [month, setMonth] = useState(new Date().getMonth() + 1)
  const [year, setYear] = useState(new Date().getFullYear())

  const generate = async () => {
    setMsg('')
    try {
      const res = await api(`/finance/payroll-runs/generate?month=${month}&year=${year}`, { method: 'POST' })
      setMsg(`Payroll ${res.period} dibuat untuk ${res.employee_count} karyawan — total ${fmtIDR(res.total_amount)}.`)
      runs.reload()
    } catch (e) { setMsg(e.message) }
  }

  return (
    <div className="card">
      <h2>Payroll (Penggajian)</h2>
      <div className="form-row row3">
        <div><label>Bulan</label><input type="number" min="1" max="12" value={month} onChange={(e) => setMonth(Number(e.target.value))} /></div>
        <div><label>Tahun</label><input type="number" value={year} onChange={(e) => setYear(Number(e.target.value))} /></div>
        <div style={{ alignSelf: 'end' }}><button className="btn" onClick={generate}>Jalankan Payroll</button></div>
      </div>
      {msg && <div className="ok-msg">{msg}</div>}
      <table style={{ marginTop: 12 }}>
        <thead><tr><th>Kode</th><th>Periode</th><th>Total</th><th>Status</th></tr></thead>
        <tbody>
          {(runs.data || []).map((r) => (
            <tr key={r.id}><td className="mono">{r.code}</td>
              <td>{r.period_year}-{String(r.period_month).padStart(2, '0')}</td>
              <td>{fmtIDR(r.total_amount)}</td><td>{r.status}</td></tr>
          ))}
          {!(runs.data || []).length && <tr><td colSpan={4} className="empty">Belum ada payroll.</td></tr>}
        </tbody>
      </table>
    </div>
  )
}

function JournalSection() {
  const jr = useFetch('/finance/journals')
  return (
    <div className="card">
      <h2>General Ledger / Jurnal</h2>
      <table>
        <thead><tr><th>Kode</th><th>Tanggal</th><th>Deskripsi</th><th>Referensi</th></tr></thead>
        <tbody>
          {(jr.data || []).map((e) => (
            <tr key={e.id}>
              <td className="mono">{e.code}</td>
              <td>{fmtDate(e.entry_date)}</td>
              <td>{e.description}</td>
              <td className="mono">{e.reference || '-'}</td>
            </tr>
          ))}
          {!(jr.data || []).length && <tr><td colSpan={4} className="empty">Belum ada jurnal.</td></tr>}
        </tbody>
      </table>
    </div>
  )
}