#!/bin/bash
# ssl_certificate_generate.sh — Generate Let's Encrypt SSL for a domain
# SH-06 FIX: Quote all variables to prevent word splitting on domain/email values

set -euo pipefail
PATH=/bin:/sbin:/usr/bin:/usr/sbin:/usr/local/bin:/usr/local/sbin:~/bin
export PATH

domain="${1:?Domain argument is required}"
email="${2:?Email argument is required}"

# Belt-and-suspenders validation (Python validates before calling this)
if [[ "$domain" =~ [^a-zA-Z0-9.\-] ]]; then
    echo "ERROR: Invalid domain '${domain}'" >&2; exit 1
fi
if [[ "$email" =~ [^a-zA-Z0-9._%+@\-] ]]; then
    echo "ERROR: Invalid email '${email}'" >&2; exit 1
fi

# SH-06 FIX: "$domain" and "$email" are quoted
certbot run -n --nginx --non-interactive --agree-tos \
    -d "${domain},www.${domain}" \
    -m "${email}" \
    --redirect