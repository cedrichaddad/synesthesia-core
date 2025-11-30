import sys
import os

# Ensure project root is in path
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

from ui.app import SynesthesiaApp

if __name__ == "__main__":
    app = SynesthesiaApp()
    app.run()
