#!/usr/bin/env python3
"""
brain_summarizer.py v2
Dosyayı 10 eşit parçaya böler, her biri için 1 Ollama çağrısı yapar.
Toplam 11 çağrı → 10-15 dakikada biter.
"""

import requests
import subprocess
import sys
import os
import argparse
from datetime import datetime

OLLAMA_API = "http://100.95.19.33:11434/api/generate"
MODEL      = "qwen3:30b-instruct"
WIN_USER   = os.environ.get("WIN_USER", "ali")
WIN_IP     = os.environ.get("WIN_IP", "100.95.19.33")
WIN_DIR    = os.environ.get("WIN_DIR", "C:/asuli-core")
NUM_CHUNKS = 10
TIMEOUT    = 300

def log(msg):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}", flush=True)

def read_brain_file(date_str):
    remote_path = f"{WIN_USER}@{WIN_IP}:{WIN_DIR}/brain_{date_str}.md"
    local_path  = f"/tmp/brain_{date_str}.md"
    log(f"Windows'tan çekiliyor: brain_{date_str}.md")
    result = subprocess.run(["scp", remote_path, local_path], capture_output=True, text=True)
    if result.returncode != 0:
        log(f"HATA: {result.stderr.strip()}")
        sys.exit(1)
    with open(local_path, "r", encoding="utf-8") as f:
        content = f.read()
    log(f"Okundu: {len(content):,} karakter / {content.count(chr(10)):,} satır")
    return content

def split_equal(content, n):
    lines = content.splitlines()
    chunk_size = max(1, len(lines) // n)
    chunks = []
    for i in range(n):
        start = i * chunk_size
        end   = start + chunk_size if i < n - 1 else len(lines)
        chunk = "\n".join(lines[start:end])
        if chunk.strip():
            chunks.append(chunk)
    log(f"Dosya {len(chunks)} parçaya bölündü (~{chunk_size} satır/parça)")
    return chunks

def call_ollama(prompt):
    try:
        resp = requests.post(
            OLLAMA_API,
            json={"model": MODEL, "prompt": prompt, "stream": False,
                  "options": {"temperature": 0.2, "num_predict": 800}},
            timeout=TIMEOUT
        )
        resp.raise_for_status()
        return resp.json().get("response", "").strip()
    except requests.exceptions.Timeout:
        return "[TIMEOUT]"
    except Exception as e:
        return f"[HATA: {e}]"

def summarize_chunk(idx, total, chunk):
    log(f"[{idx}/{total}] Özetleniyor... ({len(chunk):,} karakter)")
    prompt = f"""Aşağıdaki teknik çalışma notunu Türkçe olarak özetle.

{chunk}

KURALLAR (kesinlikle uy):
- Yanıtını YALNIZCA TÜRKÇE yaz. Başka dil kullanma.
- Maksimum 15 madde
- Sadece önemli kararlar, kurulumlar, değişiklikler
- Her madde tek cümle, net
- Gereksiz tekrar yok
- Kod bloğu, tablo veya başlık kullanma

Türkçe Özet:"""
    result = call_ollama(prompt)
    log(f"[{idx}/{total}] Tamamlandı")
    return result

def build_executive_summary(chunk_summaries, date_str):
    log("Executive summary oluşturuluyor...")
    combined = "\n\n".join([f"[Parça {i+1}]\n{s}" for i, s in enumerate(chunk_summaries)])
    prompt = f"""{date_str} tarihli çalışma notlarının parça özetleri aşağıda.
Bunlardan tek sayfalık executive summary oluştur.

{combined}

KURALLAR (kesinlikle uy):
- Yanıtını YALNIZCA TÜRKÇE yaz. Başka dil kullanma.
- Kod bloğu, tablo veya markdown başlık kullanma
- Sadece düz madde listesi

Format:
## Bugün Ne Yapıldı
- (max 7 madde)

## Alınan Kararlar
- (max 5 madde)

## Kurulan / Değişen Sistemler
- (max 5 madde)

## Sonraki Adımlar
- (max 5 madde)"""
    return call_ollama(prompt)

def write_and_send(date_str, executive, chunk_summaries):
    local_path  = f"/tmp/brain_summary_{date_str}.md"
    remote_path = f"{WIN_USER}@{WIN_IP}:{WIN_DIR}/brain_summary_{date_str}.md"
    lines = [
        f"# Brain Summary — {date_str}",
        f"_Model: {MODEL} | {datetime.now().strftime('%Y-%m-%d %H:%M')}_",
        "", "---", "", executive, "", "---", "", "## Parça Özetleri", ""
    ]
    for i, s in enumerate(chunk_summaries, 1):
        lines.append(f"### Parça {i}")
        lines.append(s)
        lines.append("")
    with open(local_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    size_kb = os.path.getsize(local_path) // 1024
    log(f"Özet yazıldı: {size_kb} KB")
    result = subprocess.run(["scp", local_path, remote_path], capture_output=True, text=True)
    if result.returncode == 0:
        log(f"Windows'a gönderildi: brain_summary_{date_str}.md")
    else:
        log(f"UYARI: Windows'a gönderilemedi — {result.stderr.strip()}")
    return local_path

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--date", default=datetime.now().strftime("%Y-%m-%d"))
    parser.add_argument("--chunks", type=int, default=NUM_CHUNKS)
    args = parser.parse_args()
    log(f"=== Brain Summarizer v2 — {args.date} ===")
    log(f"Model: {MODEL} | Parça sayısı: {args.chunks}")
    content         = read_brain_file(args.date)
    chunks          = split_equal(content, args.chunks)
    chunk_summaries = [summarize_chunk(i+1, len(chunks), c) for i, c in enumerate(chunks)]
    executive       = build_executive_summary(chunk_summaries, args.date)
    out             = write_and_send(args.date, executive, chunk_summaries)
    log(f"=== Tamamlandı → {out} ===")

    # Telegram bildirimi
    send_telegram(
        f"✅ *Brain Summary Hazır*\n"
        f"📅 Tarih: {args.date}\n"
        f"📁 `brain_summary_{args.date}.md`\n"
        f"📍 C:\\asuli-core\\\n"
        f"👉 AEIN projesine yükle"
    )




def send_telegram(msg):
    token   = os.environ.get("TG_TOKEN")
    chat_id = os.environ.get("TG_CHAT_ID")
    if not token or not chat_id:
        log("UYARI: TG_TOKEN veya TG_CHAT_ID eksik")
        return
    try:
        requests.post(
            f"https://api.telegram.org/bot{token}/sendMessage",
            json={"chat_id": chat_id, "text": msg, "parse_mode": "Markdown"},
            timeout=10
        )
        log("Telegram bildirimi gönderildi")
    except Exception as e:
        log(f"Telegram HATA: {e}")

if __name__ == "__main__":
    main()
