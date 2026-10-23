#!/bin/sh
# Run a fixed sequence of commands on the Pro Mini, then report everything it said.
#
#   usage: seq.sh <seconds per step> "cmd" "cmd" ...
#
# No daemon, no queue file, nothing that can quietly expire and leave commands unread.
# The port is opened once, the sequence is driven from this script, and the whole exchange
# is printed at the end. Opening the port can pulse DTR and reset the module, which is
# harmless here: the reset happens before the first command, and duty is set after it.
#
# This is how the duty range gets listened to. 10 s per rung is long enough to hear a rung
# and to read a meter on it:
#
#   sh seq.sh 10 "f 100" 0 10 20 30 40 50 60 70 80 90 100

PORT=/dev/ttyUSB0
LOG=/root/seq.log
DWELL=${1:-40}
shift

stty -F "$PORT" 9600 raw -echo -crtscts -hupcl || exit 1
: > "$LOG"

exec 3<> "$PORT"

( timeout $(( DWELL * ( $# + 3 ) )) cat <&3 >> "$LOG" ) &

sleep 2
printf '?\r\n' >&3
sleep 1

for c in "$@"; do
    echo "===== next command: $c =====" >> "$LOG"
    printf '%s\r\n' "$c" >&3
    sleep "$DWELL"
done

printf '0\r\n' >&3
sleep 1
echo "===== finished, duty returned to 0 percent =====" >> "$LOG"

cat "$LOG"
