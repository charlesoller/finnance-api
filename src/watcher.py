import os
import shutil
import subprocess
import time

from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer


class WatcherHandler(FileSystemEventHandler):
    """Class for restarting the SAM server on any changes"""

    def __init__(self):
        self.sam_process = None
        self.last_restart = 0
        self.restart_cooldown = (
            2  # Debounce: Prevent multiple triggers in quick succession
        )

    def on_modified(self, event):
        """Handles file modification events"""
        current_time = time.time()

        if (
            current_time - self.last_restart < self.restart_cooldown
            or "sam" in event.src_path
            or ".aws-sam" in event.src_path
        ):
            return

        if event.src_path.endswith((".py", ".yaml", ".json")):
            print(f"\nRestarting API due to changes in: {event.src_path}")
            self.restart_server()
            self.last_restart = current_time

    def kill_port_3000(self):
        """Kill any process using port 3000"""
        try:
            lsof_output = subprocess.check_output(
                ["lsof", "-ti", ":3000"], text=True
            ).strip()
            if lsof_output:
                for pid in lsof_output.split("\n"):
                    subprocess.run(["kill", "-9", pid], check=True)
        except subprocess.CalledProcessError:
            pass  # If no process is found, continue

    def clean_build_directory(self):
        """Cleans the AWS SAM build directory"""
        if os.path.exists(".aws-sam"):
            shutil.rmtree(".aws-sam", ignore_errors=True)
        os.makedirs(".aws-sam", exist_ok=True)

    def restart_server(self):
        """Stops existing SAM server and restarts it"""
        print("Stopping existing SAM local server...")

        if self.sam_process:
            self.sam_process.terminate()
            try:
                self.sam_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.sam_process.kill()

        self.kill_port_3000()  # Kill processes before restarting
        self.clean_build_directory()  # Only clean build directory

        print("Rebuilding and restarting API...")
        try:
            build_result = subprocess.run(
                ["sam", "build"], check=True, capture_output=True, text=True
            )
            if build_result.returncode != 0:
                print(f"Build failed: {build_result.stderr}")
                return

            # Start SAM API with lazy container handling
            self.sam_process = subprocess.Popen(
                [
                    "sam",
                    "local",
                    "start-api",
                    "--env-vars",
                    "env.json",
                    "--warm-containers",
                    "LAZY",
                ]
            )
            print("SAM API restarted successfully.")
        except subprocess.CalledProcessError as e:
            print(f"Error during restart: {e}")

    def is_sam_running(self):
        """Check if the SAM process is still running"""
        return self.sam_process and self.sam_process.poll() is None


if __name__ == "__main__":
    print("Starting Serverless API watcher...")

    handler = WatcherHandler()
    handler.restart_server()

    PATH = "."
    observer = Observer()
    observer.schedule(handler, PATH, recursive=True)
    observer.start()

    try:
        while True:
            time.sleep(3)
    except KeyboardInterrupt:
        print("\nShutting down...")
        if handler.sam_process:
            handler.sam_process.terminate()
        handler.kill_port_3000()
        observer.stop()

    observer.join()
