import os
import shutil
import subprocess
import time

from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer


class WatcherHandler(FileSystemEventHandler):
    """Class for restarting server on any changes"""

    def __init__(self):
        self.sam_process = None
        self.last_restart = 0
        self.restart_cooldown = 2

    def on_modified(self, event):
        current_time = time.time()
        if (
            current_time - self.last_restart < self.restart_cooldown
            or "sam" in event.src_path
            or ".aws-sam" in event.src_path
        ):
            return

        if event.src_path.endswith((".py", ".yaml", ".json")):
            print("\nRestarting API due to changes in:", event.src_path)
            self.restart_server()
            self.last_restart = current_time

    def clean_docker_containers(self):
        """Stop any running Docker containers related to SAM"""
        try:
            # Get all container IDs
            containers = subprocess.check_output(
                ["docker", "ps", "-q"], text=True
            ).split()

            # Stop each container
            for container in containers:
                subprocess.run(["docker", "stop", container], check=True)
                time.sleep(1)
        except subprocess.CalledProcessError as e:
            print(f"Warning: Error stopping Docker containers: {e}")

    def kill_port_3000(self):
        """Kill any process using port 3000"""
        try:
            # Find process using port 3000
            lsof_output = subprocess.check_output(
                ["lsof", "-i", ":3000", "-t"], text=True
            ).strip()

            if lsof_output:
                # Kill each process
                for pid in lsof_output.split("\n"):
                    subprocess.run(["kill", "-9", pid], check=True)
                time.sleep(1)
        except subprocess.CalledProcessError:
            # If no process is found or lsof fails, just continue
            pass

    def clean_build_directory(self):
        """Clean up the build directory"""
        try:
            # First kill port 3000 processes
            self.kill_port_3000()

            # Then clean up Docker containers
            self.clean_docker_containers()

            # Then remove the .aws-sam directory
            if os.path.exists(".aws-sam"):
                shutil.rmtree(".aws-sam", ignore_errors=True)

            # Create a fresh .aws-sam directory
            os.makedirs(".aws-sam", exist_ok=True)
            time.sleep(2)  # Wait for filesystem operations to complete
        except Exception as e:
            print(f"Warning: Could not clean directory: {e}")

    def restart_server(self):
        """Kill existing sam process and restart the server"""
        print("Stopping existing sam local server...")

        if self.sam_process:
            self.sam_process.terminate()
            try:
                self.sam_process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                self.sam_process.kill()

        self.clean_build_directory()

        print("Rebuilding and restarting API...")
        try:
            subprocess.run(
                ["sam", "build"],
                check=True,
                stderr=subprocess.PIPE,  # Capture stderr
                text=True,
            )

            time.sleep(2)  # Give time for the build to complete fully
            # Add --warm-containers LAZY to handle container cleanup better
            self.sam_process = subprocess.Popen(
                [
                    "sam",
                    "local",
                    "start-api",
                    "--env-vars",
                    "env.json",
                    "--warm-containers",
                    "LAZY",
                ],
            )
        except subprocess.CalledProcessError as e:
            print(f"Error during restart: {e}")


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
            time.sleep(1)
            if handler.sam_process and handler.sam_process.poll() is not None:
                print("SAM process terminated unexpectedly. Restarting...")
                handler.restart_server()
    except KeyboardInterrupt:
        print("\nShutting down...")
        if handler.sam_process:
            handler.sam_process.terminate()
        handler.kill_port_3000()  # Make sure to kill port 3000 on exit
        observer.stop()

    observer.join()
