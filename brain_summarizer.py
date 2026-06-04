#!/usr/bin/env python3
import sys, re, subprocess, requests, os
from datetime import datetime

OLLAMA_API = "http://100.95.19.33:11434/api/generate"
MODEL = "qwen3:30b-instruct"
WIN_USER = "ali"
WIN_IP = "100.95.19.33"
WIN_DIR = "C:/asuli-core"
TG_TOKEN = os.environ.get("TG_TOKEN", "")
TG_CHAT_ID = os.environ.get("TG_CHAT_ID", "")

def log(msg): print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}", flush=True)

def get_date():
    for i, arg in enumerate(sys.argv):
        if arg == "--date" and i+1 < len(sys.argv):
            return sys.argv[i+1]
    return datetime.now().strftime("%Y-%m-%d")

def ollama(prompt):
    r = requests.post(OLLAMA_API, json={
        "model": MODEL, "prompt": prompt, "stream": False,
        "options": {"temperature": 0.3, "num_predict": 2048}
    }, timeout=300)
    return r.json()["response"].strip()

def send_telegram(msg):
    if TG_TOKEN and TG_CHAT_ID:
        requests.post(f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage",
                      json={"chat_id": TG_CHAT_ID, "text": msg})

def detect_project(filename):
    f = filename.lower()
    if any(x in f for x in ["aein", "ali_reset", "private"]): return "AEIN / Kariyer"
    if any(x in f for x in ["asuli", "roadmap", "changelog", "pdf_pilot"]): return "Asuli"
    if any(x in f for x in ["medium", "medium_brain"]): return "Medium"
    if any(x in f for x in ["reels", "fb.brain", "reel"]): return "Reels Pipeline"
    if any(x in f for x in ["telegram", "tbrain"]): return "Telegram Bot"
    if "morning" in f: return "Morning Briefing"
    if any(x in f for x in ["brainos", "brain_sync"]): return "BrainOS Tools"
    return "Genel"

date_str = get_date()
log(f"=== Brain Summarizer v3 — {date_str} ===")
log(f"Model: {MODEL} | Dosya bazlı özetleme")

# Windows'tan çek
remote_file = f"{WIN_DIR}/brain_{date_str}.md"
local_file = f"/tmp/brain_{date_str}.md"
r = subprocess.run(["scp", f"{WIN_USER}@{WIN_IP}:{remote_file}", local_file], capture_output=True)
if r.returncode != 0:
    log(f"HATA: {r.stderr.decode()}"); sys.exit(1)

with open(local_file, "r", encoding="utf-8") as f:
    content = f.read()
log(f"Okundu: {len(content):,} karakter")

# Dosya bölümlerine ayır
sections = []
parts = re.split(r'\n---\n## ', content)
for part in parts[1:]:
    lines = part.split('\n', 1)
    filename = lines[0].strip()
    body = lines[1].strip() if len(lines) > 1 else ""
    if len(body) > 100:
        sections.append((filename, body))
log(f"{len(sections)} dosya bölümü bulundu")

# Her dosyayı ayrı özetle
file_summaries = []
for i, (filename, body) in enumerate(sections, 1):
    project = detect_project(filename)
    log(f"[{i}/{len(sections)}] [{project}] {filename} ({len(body):,} karakter)")
    prompt = f"""Sen bir teknik proje asistanısın. Aşağıdaki proje notunu okuyan kıdemli bir mühendis gibi özetle.

Dosya: {filename}
Proje: {project}

---
{body[:8000]}
---

KURALLAR:
- YALNIZCA TÜRKÇE yaz, başka dil kullanma
- Maksimum 8 madde
- Sadece önemli kararlar, kurulumlar, değişiklikler
- Her madde tek cümle, net ve özlü
- Kod bloğu, tablo, markdown başlık kullanma
- Düz madde listesi

Türkçe Özet:"""
    summary = ollama(prompt)
    file_summaries.append((project, filename, summary))
    log(f"[{i}/{len(sections)}] Tamamlandı")

# Proje bazlı gruplama
log("Executive summary oluşturuluyor...")
project_groups = {}
for project, filename, summary in file_summaries:
    project_groups.setdefault(project, []).append(f"[{filename}]\n{summary}")

grouped_text = ""
for project, summaries in project_groups.items():
    grouped_text += f"\n### {project}\n" + "\n".join(summaries) + "\n"

exec_prompt = f"""{date_str} tarihli proje notlarının özeti aşağıda, proje bazlı gruplandırılmış.
Her proje için kısa, net executive summary oluştur.

{grouped_text[:12000]}

KURALLAR:
- YALNIZCA TÜRKÇE yaz
- Her proje başlığını koru
- Her proje altında maksimum 5 madde
- Kod bloğu, tablo kullanma
- Sadece düz madde listesi

Format:
## [Proje Adı]
- madde
- madde"""

exec_summary = ollama(exec_prompt)

# Dosyaya yaz
output_file = f"/tmp/brain_summary_{date_str}.md"
with open(output_file, "w", encoding="utf-8") as f:
    f.write(f"# Brain Summary — {date_str}\n")
    f.write(f"_Model: {MODEL} | {datetime.now().strftime('%Y-%m-%d %H:%M')}_\n\n---\n\n")
    f.write(exec_summary)
    f.write("\n\n---\n\n## Dosya Özetleri\n\n")
    for project, filename, summary in file_summaries:
        f.write(f"### [{project}] {filename}\n{summary}\n\n")

size_kb = os.path.getsize(output_file) // 1024
log(f"Özet yazıldı: {size_kb} KB")

r = subprocess.run(["scp", output_file, f"{WIN_USER}@{WIN_IP}:{WIN_DIR}/"], capture_output=True)
if r.returncode == 0:
    log(f"Windows'a gönderildi: brain_summary_{date_str}.md")
else:
    log("HATA: Windows'a gönderilemedi")

log(f"=== Tamamlandı → {output_file} ===")
send_telegram(f"✅ Brain Summary Hazır\n📅 Tarih: {date_str}\n📁 brain_summary_{date_str}.md\n📍 C:\\asuli-core\\\n👉 AEIN projesine yükle")
log("Telegram bildirimi gönderildi")
