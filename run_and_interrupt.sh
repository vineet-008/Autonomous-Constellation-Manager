venv/bin/python -m examples.test_flight > debug_output.txt 2>&1 &
PID=$!
sleep 5
kill -INT $PID
