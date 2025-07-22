# Aegis Swarm 2.0 - Main Application Entry Point (Final Cleaned Version)
# This is the single script that users will run to launch the application.

import sys

try:
    # This is the standard way to start a PyQt application.
    from PyQt5.QtWidgets import QApplication
    from gui.main_window import MainWindow

    # This standard Python construct ensures that run_application() is called
    # only when this script is executed directly.
    if __name__ == '__main__':
        print("Launching Aegis Swarm 2.0 Tactical AI Laboratory...")
        
        # Create the application instance.
        app = QApplication(sys.argv)
        
        # Create an instance of our main window.
        main_window = MainWindow()
        
        # Show the window on the screen.
        main_window.show()
        
        # Start the Qt event loop and ensure a clean exit.
        sys.exit(app.exec_())

except ImportError as e:
    print("FATAL ERROR: A required library is not installed.", file=sys.stderr)
    if 'PyQt5' in str(e):
        print("Please make sure you have PyQt5 installed: 'pip install PyQt5'", file=sys.stderr)
    else:
        print("An unexpected import error occurred. Please check your environment.", file=sys.stderr)
    print(f"Original error: {e}", file=sys.stderr)
    sys.exit(1)
except Exception as e:
    print(f"An unexpected fatal error occurred: {e}", file=sys.stderr)
    # In a real application, you would log this to a file.
    sys.exit(1)