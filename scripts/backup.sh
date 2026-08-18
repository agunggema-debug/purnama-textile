#!/usr/bin/env bash
# ============================================================================
# Backup otomatis database PostgreSQL ke NAS untuk Sistem ERP Purnama Textile.
# Jalankan melalui cron:
#   0 * * * * /opt/purnama-erp/scripts/backup.sh
#   30 2 * * * /opt/purnama-erp/scripts/backup.sh
# ============================================================================
set -euo pipefail

# --- Konfigurasi (sesuaikan untuk intranet pabrik) ---
DB_USER="${POSTGRES_USER:-purnama}"
DB_NAME="${POSTGRES_DB:-purnama_erp}"
DB_HOST="${POSTGRES_HOST:-db}"
DB_PORT="${POSTGRES_PORT:-5432}"

# Direktori tujuan (mount NAS). Contoh mount: /mnt/nas/purnama-backup
BACKUP_DIR="${BACKUP_DIR:-/mnt/nas/purnama-backup}"
RETENTION_DAYS="${RETENTION_DAYS:-7}"

STAMP="$(date +%Y%m%d_%H%M%S)"
FILENAME="${DB_NAME}_${STAMP}.sql.gz"

mkdir -p "${BACKUP_DIR}"

echo "[$(date)] Mulai backup ${DB_NAME} -> ${BACKUP_DIR}/${FILENAME}"

# dump lalu kompres
pg_dump -U "${DB_USER}" -h "${DB_HOST}" -p "${DB_PORT}" "${DB_NAME}" \
  | gzip -9 > "${BACKUP_DIR}/${FILENAME}"

echo "[$(date)] Backup selesai: $(du -h "${BACKUP_DIR}/${FILENAME}" | cut -f1)"

# Hapus backup lebih lama dari masa retensi
find "${BACKUP_DIR}" -name "${DB_NAME}_*.sql.gz" -mtime +"${RETENTION_DAYS}" -delete

echo "[$(date)] Selesai."
