#!/bin/bash
#
# Multi-Agent Platform - Simple Start Script
#

APP_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PID_FILE="/tmp/multi-agent.pid"
LOG_FILE="/tmp/multi-agent.log"

case "$1" in
    start)
        if [ -f "$PID_FILE" ] && kill -0 $(cat "$PID_FILE") 2>/dev/null; then
            echo "Server already running (PID: $(cat $PID_FILE))"
        else
            cd "$APP_DIR"
            nohup python3 -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 > "$LOG_FILE" 2>&1 &
            echo $! > "$PID_FILE"
            echo "Server started! (PID: $!)"
            sleep 1
            echo ""
            echo "API:        http://localhost:8000"
            echo "API Docs:   http://localhost:8000/docs"
        fi
        ;;
    stop)
        if [ -f "$PID_FILE" ]; then
            kill $(cat "$PID_FILE") 2>/dev/null
            rm -f "$PID_FILE"
            echo "Server stopped"
        else
            echo "Server not running"
        fi
        ;;
    restart)
        $0 stop
        sleep 1
        $0 start
        ;;
    status)
        if [ -f "$PID_FILE" ] && kill -0 $(cat "$PID_FILE") 2>/dev/null; then
            echo "Server is running (PID: $(cat $PID_FILE))"
            curl -s http://localhost:8000/ | python3 -m json.tool
        else
            echo "Server is not running"
        fi
        ;;
    logs)
        tail -f "$LOG_FILE"
        ;;
    *)
        echo "Multi-Agent Platform Control"
        echo ""
        echo "Usage: ./server.sh {start|stop|restart|status|logs}"
        echo ""
        echo "Commands:"
        echo "  start    - Start the server"
        echo "  stop     - Stop the server"
        echo "  restart  - Restart the server"
        echo "  status   - Check server status"
        echo "  logs     - View live logs"
        ;;
esac
