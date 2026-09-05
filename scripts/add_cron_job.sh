#!/bin/bash
# add_cron_job.sh — Install a cron job for a user
# SH-05 FIX:
#   - Use mktemp for the temporary crontab file (absolute path, no race condition)
#   - Quote all variables
#   - Validate username input

set -euo pipefail
PATH=/bin:/sbin:/usr/bin:/usr/sbin:/usr/local/bin:/usr/local/sbin:~/bin
export PATH

username="${1:?Username argument is required}"
croncommand="${2:?Cron command argument is required}"

# Belt-and-suspenders validation (Python already validates before calling this)
if [[ "$username" =~ [^a-z0-9_-] ]]; then
    echo "ERROR: Invalid username '${username}'" >&2; exit 1
fi

# Ensure log directory exists
mkdir -m 755 -p "/home/${username}/crobjobs/logs"
chown -R "${username}:${username}" "/home/${username}/crobjobs/logs"

# SH-05 FIX: Use a secure temp file (absolute path, auto-cleaned up)
TMPFILE=$(mktemp /tmp/saspanel_cron_XXXXXX)
trap 'rm -f "${TMPFILE}"' EXIT

# Write only the new cron entry
echo "${croncommand}" > "${TMPFILE}"
crontab -u "${username}" "${TMPFILE}"

echo "Cron job installed for ${username}."