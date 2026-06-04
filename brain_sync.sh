#!/bin/bash
SYNC_DIR="/home/ali/MDbackup"
SEARCH_ROOT="/home/ali"
LOG_FILE="$SYNC_DIR/sync.log"
DATE_TAG=$(date '+%Y-%m-%d')
TODAY_DIR="$SYNC_DIR/$DATE_TAG"
WIN_IP="${WIN_IP:-100.95.19.33}"
WIN_USER="${WIN_USER:-ali}"
WIN_DIR="${WIN_DIR:-C:/asuli-core}"
rm -rf "$TODAY_DIR" && mkdir -p "$TODAY_DIR"
log() { echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"; }
log "=========================================="; log "Sync başladı — $DATE_TAG"
DIRS=$(find "$SEARCH_ROOT" \( -name ".git" -o -name ".cache" -o -name ".local" -o -name ".venv" -o -name "venv" -o -name "node_modules" -o -name "__pycache__" -o -name ".config" -o -name "snap" -o -name ".var" -o -name "MDbackup" -o -name "archive" -o -name "backup" -o -name "backups" -o -name "markdown" -o -name "staging" -o -name "epub_validation" -o -name "Downloads" -o -name ".gitkraken" \) -prune -o -name "*.md" -print0 2>/dev/null | xargs -0 -I{} dirname {} | sort -u)
COPIED=0
while IFS= read -r DIR; do
  NEWEST=$(find "$DIR" -maxdepth 1 -name "*.md" -printf '%T@ %p\n' 2>/dev/null | sort -rn | head -1 | cut -d' ' -f2-)
  if [ -n "$NEWEST" ]; then
    REL_PATH="${NEWEST#$SEARCH_ROOT/}"; SAFE_NAME=$(echo "$REL_PATH" | tr '/' '_')
    cp "$NEWEST" "$TODAY_DIR/$SAFE_NAME"; COPIED=$((COPIED + 1)); log "Kopyalandı: $NEWEST"
  fi
done <<< "$DIRS"
log "Kopyalanan: $COPIED dosya"
MERGED="$SYNC_DIR/brain_$(date '+%Y-%m-%d').md"
echo "# BrainOS Master — $(date '+%Y-%m-%d')" > "$MERGED"; echo "" >> "$MERGED"
for F in "$TODAY_DIR"/*.md; do FNAME=$(basename "$F"); echo "---" >> "$MERGED"; echo "## $FNAME" >> "$MERGED"; echo "" >> "$MERGED"; cat "$F" >> "$MERGED"; echo "" >> "$MERGED"; done
log "Merge tamamlandı: $MERGED"
ssh "$WIN_USER@$WIN_IP" "mkdir -p '$WIN_DIR'" 2>/dev/null
scp "$MERGED" "$WIN_USER@$WIN_IP:$WIN_DIR/" && log "Windows'a gönderildi: $WIN_DIR/$(basename $MERGED)" || log "HATA: Windows'a gönderilemedi"
log "Summarizer başlatılıyor..."
python3 /home/ali/bin/brain_summarizer.py --date "$(date '+%Y-%m-%d')" && log "Summarizer tamamlandı." || log "HATA: Summarizer başarısız."
