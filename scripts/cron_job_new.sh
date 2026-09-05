#!/bin/bash
# cron_job_new.sh — Alternative cron job helper
# SH-NEW FIX:
#   - All variables quoted to prevent word splitting / injection
#   - Input validated against whitelist before use
#   - /etc/cron.allow write uses validated username
#   - Unquoted $CRON_FILE references fixed

set -euo pipefail
PATH=/bin:/sbin:/usr/bin:/usr/sbin:/usr/local/bin:/usr/local/sbin:~/bin
export PATH

username="${1:?Username argument is required}"
croncommand="${2:?Cron command argument is required}"

# Validate username against strict whitelist
if [[ ! "${username}" =~ ^[a-z0-9_-]{1,64}$ ]]; then
    echo "ERROR: Invalid username '${username}'" >&2
    exit 1
fi

# Add to cron.allow safely
echo "${username}" >> /etc/cron.allow

CRON_FILE="/var/spool/cron/${username}"

# Create cron file if missing
if [[ ! -f "${CRON_FILE}" ]]; then
    echo "Cron file for ${username} does not exist, creating..."
    touch "${CRON_FILE}"
    chmod 600 "${CRON_FILE}"
    /usr/bin/crontab "${CRON_FILE}"
fi

# Append the job if the placeholder pattern isn't already present
if ! grep -qi "cleanup_script" "${CRON_FILE}"; then
    echo "Updating cron job for cleaning temporary files"
    echo "* * * * * php index.php >> /home/${username}/crobjobs/logs/logg.cron" >> "${CRON_FILE}"
fi

mkdir -m 755 -p "/home/${username}/crobjobs/logs"
chown -R "www-data:www-data" "/home/${username}/crobjobs/logs/"
chown -R "${username}:${username}" "/home/${username}/crobjobs/logs/"

echo "Cron job configured for ${username}."