#!/bin/bash
SYNC_DIR="/home/ali/MDbackup"
SEARCH_ROOT="/home/ali"
LOG_FILE="$SYNC_DIR/sync.log"
DATE_TAG=$(date '+%Y-%m-%d')
TODAY_DIR="$SYNC_DIR/$DATE_TAG"
mkdir -p "$TODAY_DIR"
log() { echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"; }
log "=========================================="
log "Sync başladı — $DATE_TAG"
FOUND=0; COPIED=0
while IFS= read -r -d '' FILE; do
  FOUND=$((FOUND + 1))
  REL_PATH="${FILE#$SEARCH_ROOT/}"
  SAFE_NAME=$(echo "$REL_PATH" | tr '/' '_')
  DEST="$TODAY_DIR/$SAFE_NAME"
  if [ -f "$DEST" ]; then
    SRC_MOD=$(stat -c %Y "$FILE"); DST_MOD=$(stat -c %Y "$DEST")
    [ "$SRC_MOD" -le "$DST_MOD" ] && continue
  fi
  cp "$FILE" "$DEST"; COPIED=$((COPIED + 1))
  log "Kopyalandı: $FILE"
done < <(find "$SEARCH_ROOT" \( -name ".git" -o -name "node_modules" -o -name ".venv" -o -name "__pycache__" -o -name ".cache" -o -name ".local" -o -name ".mozilla" -o -name ".config" \) -prune -o -name "*.md" -mtime -1 -print0 2>/dev/null)
log "Bulunan: $FOUND | Kopyalanan: $COPIED"
{ echo "# Brain Sync — $DATE_TAG"; echo ""; for F in "$TODAY_DIR"/*.md; do FNAME=$(basename "$F"); [ "$FNAME" = "_OZET.md" ] && continue; echo "- $FNAME"; done; } > "$TODAY_DIR/_OZET.md"
log "Tamamlandı."

# --- MERGE ---
MERGED="$SYNC_DIR/brain_$(date '+%Y-%m-%d').md"
echo "# BrainOS Master — $(date '+%Y-%m-%d')" > "$MERGED"
echo "" >> "$MERGED"
for F in "$TODAY_DIR"/*.md; do
  FNAME=$(basename "$F")
  [ "$FNAME" = "_OZET.md" ] && continue
  echo "---" >> "$MERGED"
  echo "## $FNAME" >> "$MERGED"
  echo "" >> "$MERGED"
  cat "$F" >> "$MERGED"
  echo "" >> "$MERGED"
done
log "Merge tamamlandı: $MERGED"

# --- WINDOWS'A GONDER ---
WIN_IP="${WIN_IP:-YOUR_WINDOWS_TAILSCALE_IP}"
WIN_DIR="${WIN_DIR:-C:/asuli-core}"
WIN_USER="${WIN_USER:-YOUR_USERNAME}"

# asuli-core dizini yoksa oluştur
ssh "$WIN_USER@$WIN_IP" "mkdir -p '$WIN_DIR'" 2>/dev/null

# Merge dosyasını gönder
scp "$MERGED" "$WIN_USER@$WIN_IP:$WIN_DIR/" && \
  log "Windows'a gönderildi: $WIN_DIR/$(basename $MERGED)" || \
  log "HATA: Windows'a gönderilemedi — Tailscale aktif mi?"
