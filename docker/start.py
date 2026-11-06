"""Supervise local Nginx + Uvicorn so one Docker image needs only one public port."""
import signal
import subprocess
import sys
import time


def main() -> int:
    stopping = False
    children = []

    def stop(signum, frame):
        nonlocal stopping
        stopping = True

    signal.signal(signal.SIGTERM, stop)
    signal.signal(signal.SIGINT, stop)
    try:
        children.append(subprocess.Popen([
            sys.executable, '-m', 'uvicorn', 'app.main:app', '--host', '127.0.0.1',
            '--port', '8000', '--workers', '1', '--no-proxy-headers',
        ]))
        children.append(subprocess.Popen([
            'nginx', '-c', '/app/docker/nginx.conf', '-g', 'daemon off;',
        ]))
        while not stopping:
            for child in children:
                result = child.poll()
                if result is not None:
                    print(f'Child process stopped unexpectedly: pid={child.pid}, code={result}', file=sys.stderr)
                    return result if result != 0 else 1
            time.sleep(0.25)
        return 0
    finally:
        for child in children:
            if child.poll() is None:
                child.terminate()
        deadline = time.monotonic() + 15
        for child in children:
            try:
                child.wait(timeout=max(0.1, deadline - time.monotonic()))
            except subprocess.TimeoutExpired:
                child.kill()
                child.wait()


if __name__ == '__main__':
    raise SystemExit(main())
