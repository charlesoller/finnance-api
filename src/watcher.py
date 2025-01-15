import subprocess
import time

from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer


class WatcherHandler(FileSystemEventHandler):
    """Class for restarting server on any changes"""

    def on_modified(self, event):
        """Method for handling restarting of server"""
        # Ignore files in the "sam" process (e.g., logs, temp files)
        if "sam" in event.src_path:
            return

        if event.src_path.endswith((".py", ".yaml", ".json")):
            print(
                """
__________                 __                 __  .__                    _____ __________.___ 
\______   \ ____   _______/  |______ ________/  |_|__| ____    ____     /  _  \\______   \   |
 |       _// __ \ /  ___/\   __\__  \\_  __ \   __\  |/    \  / ___\   /  /_\  \|     ___/   |
 |    |   \  ___/ \___ \  |  |  / __ \|  | \/|  | |  |   |  \/ /_/  > /    |    \    |   |   |
 |____|_  /\___  >____  > |__| (____  /__|   |__| |__|___|  /\___  /  \____|__  /____|   |___|
        \/     \/     \/            \/                    \//_____/           \/              
            """
            )
            self.restart_server()

    def restart_server(self):
        """Kill existing sam process and restart the server"""
        print("Stopping any existing sam local server...")

        # Find and kill any existing `sam local start-api` process
        try:
            subprocess.run(["pkill", "-f", "sam local start-api"], check=True)
        except subprocess.CalledProcessError:
            pass  # If no process is running, just ignore it

        print("Rebuilding and restarting API...")
        subprocess.run(["sam", "build"], check=True)

        # Run the server in the background
        self.sam_process = subprocess.Popen(["sam", "local", "start-api"])


if __name__ == "__main__":
    print(
        """
  _________ __                 __  .__                   _________                               .__                            _____ __________.___ 
 /   _____//  |______ ________/  |_|__| ____    ____    /   _____/ ______________  __ ___________|  |   ____   ______ ______   /  _  \\______   \   |
 \_____  \\   __\__  \\_  __ \   __\  |/    \  / ___\   \_____  \_/ __ \_  __ \  \/ // __ \_  __ \  | _/ __ \ /  ___//  ___/  /  /_\  \|     ___/   |
 /        \|  |  / __ \|  | \/|  | |  |   |  \/ /_/  >  /        \  ___/|  | \/\   /\  ___/|  | \/  |_\  ___/ \___ \ \___ \  /    |    \    |   |   |
/_______  /|__| (____  /__|   |__| |__|___|  /\___  /  /_______  /\___  >__|    \_/  \___  >__|  |____/\___  >____  >____  > \____|__  /____|   |___|
        \/           \/                    \//_____/           \/     \/                 \/                \/     \/     \/          \/                                                                   
    """
    )

    # Initial startup run
    subprocess.run(["sam", "build"], check=True)

    # Start the server in the background
    subprocess.Popen(["sam", "local", "start-api"])

    # Watch the directory for changes
    PATH = "."
    event_handler = WatcherHandler()
    observer = Observer()
    observer.schedule(event_handler, PATH, recursive=True)
    observer.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()

    observer.join()
