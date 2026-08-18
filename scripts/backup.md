# Essay on Backup Strategy — Purnama Textile ERP (On-Premise)

## Tujuan
PRD §2 mensyaratkan *backup otomatis* database (dump) harian/per jam ke perangkat
NAS terpisah, dengan mitigasi kegagalan hardware (RAID, server standby).

## Arsitektur
- Database PostgreSQL berjalan dalam container Docker (`pt_db`).
- Volume data persisten disimpan pada `pgdata` (lihat `docker-compose.yml`).
- Backup berupa **logical dump** (`pg_dump` dikompres gzip) yang dapat direstore
  ke instance baru kapan saja.

## Cara Kerja Backup
Script di `scripts/backup.sh` (Linux/container) akan:
1. Membuat snapshot database dengan `pg_dump`.
2. Mengompresnya dengan `gzip -9`.
3. Menyimpannya ke mount NAS (default `/mnt/nas/purnama-backup`).
4. Menghapus backup yang lebih lama dari masa retensi (default 7 hari).

Contoh konfigurasi **cron job**:
```cron
# Backup per jam (mode budget)
0 * * * * /opt/purnama-erp/scripts/backup.sh

# Backup harian (mode lengkap)
30 2 * * * /opt/purnama-erp/scripts/backup.sh
```

Untuk Windows on-premise, gunakan `scripts/backup.ps1` dengan Task Scheduler.

## Restore
```bash
gunzip -c <backup>.sql.gz | docker exec -i pt_db psql -U purnama -d purnama_erp
```

## Mitigasi & Catatan
- Salin mount NAS ke **dua lokasi fisik** berbeda (redundansi).
- Uji restore secara berkala (setidaknya bulanan).
- Aktifkan `pg_wal` / continuous archiving bila transaksi kritis per jam.
- RAID disk pada server penyimpanan + server standby untuk high availability.
