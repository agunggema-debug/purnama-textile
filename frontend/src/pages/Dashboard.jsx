import { useFetch } from '../hooks.js'
import { fmtIDR } from '../api.js'

function Stat({ label, value, sub }) {
  return (
    <div className="stat-card">
      <div className="label">{label}</div>
      <div className="value">{value ?? '…'}</div>
      {sub && <div className="sub">{sub}</div>}
    </div>
  )
}

const M = ({ children }) => (<div className="card"><h2>{children}</h2></div>)

export default function Dashboard({ user }) {
  const inv = useFetch('/warehouse/inventory')
  const ap = useFetch('/finance/ap/overview')
  const ar = useFetch('/finance/ar/overview')
  const pl = useFetch('/finance/reports/profit-loss')
  const mps = useFetch('/ppic/mps')
  const po = useFetch('/purchasing/po')
  const pnl = pl.data || {}

  const totalStock = (inv.data || []).reduce((s, i) => s + Number(i.on_hand || 0), 0)
  const totalAp = (ap.data || []).reduce((s, i) => s + Number(i.balance || 0), 0)
  const totalAr = (ar.data || []).reduce((s, i) => s + Number(i.balance || 0), 0)

  return (
    <div>
      <h1>Dashboard Operasional</h1>

      <div className="cards">
        <Stat label="Total On-Hand Stok" value={totalStock.toLocaleString('id-ID')} sub="unit seluruh lokasi" />
        <Stat label="Piutang (AR)" value={fmtIDR(totalAr)} sub="saldo tagihan pelanggan" />
        <Stat label="Hutang (AP)" value={fmtIDR(totalAp)} sub="saldo utang ke vendor" />
        <Stat label="Pendapatan" value={fmtIDR(pnl.revenue)} sub="dari jurnal" />
      </div>

      <div className="grid" style={{ gridTemplateColumns: '1fr 1fr' }}>
        <M>Jadwal Produksi (MPS)</M>
        <div className="card">
          <h2>Ringkasan</h2>
          <table>
            <tbody>
              <tr><td>Baris MPS terdaftar</td><td>{(mps.data || []).length}</td></tr>
              <tr><td>Laba Bersih (P&amp;L)</td><td>{fmtIDR(pnl.net_profit)}</td></tr>
              <tr><td>Total PO</td><td>{(po.data || []).length}</td></tr>
            </tbody>
          </table>
        </div>
      </div>

      <div className="card">
        <h2>Stok per Produk</h2>
        <table>
          <thead>
            <tr><th>Kode</th><th>Produk</th><th>Lokasi</th><th>On-Hand</th><th>Reserved</th></tr>
          </thead>
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
    </div>
  )
}
