import subprocess
import sys
import time
import socket
import webview
import atexit
import os

STREAMLIT_PORT = 8501
STREAMLIT_URL = f"http://localhost:{STREAMLIT_PORT}"
STREAMLIT_APP = "ElectroGalindez.py"


def is_port_open(host: str, port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex((host, port)) == 0


def wait_for_server(host="localhost", port=8501, timeout=20):
    start_time = time.time()

    while time.time() - start_time < timeout:
        if is_port_open(host, port):
            return True
        time.sleep(0.3)

    return False


def start_streamlit():
    cmd = [
        sys.executable,
        "-m",
        "streamlit",
        "run",
        STREAMLIT_APP,
        "--server.headless=true",
        f"--server.port={STREAMLIT_PORT}",
        "--browser.gatherUsageStats=false",
        "--client.toolbarMode=minimal",
    ]

    creationflags = 0

    if os.name == "nt":
        creationflags = subprocess.CREATE_NO_WINDOW

    process = subprocess.Popen(
        cmd,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        creationflags=creationflags
    )

    return process


def main():
    print("🚀 Iniciando aplicación desktop...")

    streamlit_process = start_streamlit()

    def cleanup():
        print("🧹 Cerrando Streamlit...")
        try:
            streamlit_process.kill()
        except Exception:
            pass

    atexit.register(cleanup)

    print("⏳ Esperando a Streamlit...")

    if not wait_for_server(port=STREAMLIT_PORT):
        print("❌ Streamlit no respondió a tiempo")
        cleanup()
        return

    print("✅ Streamlit listo")

    webview.create_window(
        title="ElectroGalíndez",
        url=STREAMLIT_URL,
        width=1200,
        height=800,
        min_size=(900, 600),
        resizable=True
    )

    webview.start()

    print("👋 Aplicación cerrada")


if __name__ == "__main__":
    main()