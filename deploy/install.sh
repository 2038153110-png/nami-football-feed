#!/bin/sh
# Install collector to /opt/nami-collector. Does not print or copy secrets.
# Usage (on the target server):
#   sudo sh deploy/install.sh
set -eu

ROOT="$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)"
DEST="${DEST:-/opt/nami-collector}"
ENV_FILE="${ENV_FILE:-/etc/nami-collector.env}"
OUT_DIR="${OUT_DIR:-/var/lib/nami-collector}"

if [ "$(id -u)" -ne 0 ]; then
  echo "run as root: sudo sh deploy/install.sh" >&2
  exit 1
fi

mkdir -p "$DEST" "$OUT_DIR"
cp "$ROOT/collector/collect.py" "$DEST/collect.py"
chmod 755 "$DEST/collect.py"

if [ ! -f "$ENV_FILE" ]; then
  umask 077
  cat >"$ENV_FILE" <<EOF
NAMI_USER=
NAMI_SECRET=
NAMI_HOST=https://open.sportnanoapi.com
OUT_DIR=$OUT_DIR
ALLOW_FOTMOB_FALLBACK=1
EOF
  chmod 600 "$ENV_FILE"
  echo "created $ENV_FILE — fill NAMI_USER and NAMI_SECRET, do not paste them into chat"
fi

cp "$ROOT/deploy/nami-collector.service" /etc/systemd/system/nami-collector.service
cp "$ROOT/deploy/nami-collector.timer" /etc/systemd/system/nami-collector.timer
systemctl daemon-reload
systemctl enable --now nami-collector.timer
systemctl start nami-collector.service || true

echo "installed $DEST"
echo "timer: systemctl status nami-collector.timer"
echo "output: $OUT_DIR"
echo "acceptance: ALLOW_FOTMOB_FALLBACK=1 python3 $DEST/collect.py --skip-nami --out $OUT_DIR"
