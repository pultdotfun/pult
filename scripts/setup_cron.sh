#!/bin/bash

# Add backup cron job
(crontab -l 2>/dev/null; echo "0 2 * * * /app/scripts/backup.py") | crontab -

# Add log rotation
cat << EOF > /etc/logrotate.d/pult
/app/logs/*.log {
    daily
    rotate 7
    compress
    delaycompress
    missingok
    notifempty
    create 0640 appuser appuser
}
EOF 