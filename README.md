# brainos-tools

Automation tools for collecting and syncing Markdown files from Fedora to Windows.

## brain_sync.sh

Runs every morning via cron. Scans all `.md` files modified in the last 24 hours, merges them into a single file, and sends it to a Windows machine via SSH/SCP over Tailscale.

## Setup

Set your environment variables before running:

    export WIN_IP="YOUR_WINDOWS_TAILSCALE_IP"
    export WIN_USER="YOUR_USERNAME"
    export WIN_DIR="C:/your-target-folder"

Run manually:

    bash brain_sync.sh

## Automated Daily Run

Open crontab:

    crontab -e

Add this line:

    0 7 * * * WIN_IP=x.x.x.x WIN_USER=ali WIN_DIR=C:/asuli-core /home/ali/bin/brain_sync.sh

## Prerequisites

- Fedora Linux
- Windows with OpenSSH Server enabled
- Tailscale installed on both machines
- SSH key authentication configured (passwordless)

## Output

    /home/ali/MDbackup/
        2026-05-28/          # daily collected files
        brain_2026-05-28.md  # merged single file, sent to Windows
        sync.log             # operation log

## Related

- Medium article: coming soon
- Author: alielmali78-prog

## License

MIT
