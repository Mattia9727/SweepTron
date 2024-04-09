"""
# Prerequisites:
pip3 install pywin32 pyinstaller

# Build:
pyinstaller.exe --onefile --runtime-tmpdir=. --hidden-import win32timezone myservice.py

# With Administrator privilges
# Install:
dist\myservice.exe install

# Start:
dist\myservice.exe start

# Install with autostart:
dist\myservice.exe --startup delayed install

# Debug:
dist\myservice.exe debug

# Stop:
dist\myservice.exe stop

# Uninstall:
dist\myservice.exe remove


"""
import sys
import time

import win32serviceutil  # ServiceFramework and commandline helper
import win32service  # Events
import servicemanager  # Simple setup and logging

from main import main


class MyService:
    """Silly little application stub"""
    def stop(self):
        """Stop the service"""
        self.running = False

    def run(self):
        """Main service loop. This is where work is done!"""
        self.running = True
        while self.running:
            time.sleep(10)  # Important work
            servicemanager.LogInfoMsg("Service running...")
            main()
            self.stop()


class MyServiceFramework(win32serviceutil.ServiceFramework):

    _svc_name_ = 'SweepTron_Transfer'
    _svc_display_name_ = 'SweepTron: Data transfer service.'

    def SvcStop(self):
        """Stop the service"""
        self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)
        self.service_impl.stop()
        self.ReportServiceStatus(win32service.SERVICE_STOPPED)

    def SvcDoRun(self):
        """Start the service; does not return until stopped"""
        self.ReportServiceStatus(win32service.SERVICE_START_PENDING)
        self.service_impl = MyService()
        self.ReportServiceStatus(win32service.SERVICE_RUNNING)
        # Run the service
        self.service_impl.run()


def init():
    if len(sys.argv) == 1:
        servicemanager.Initialize()
        servicemanager.PrepareToHostSingle(MyServiceFramework)
        servicemanager.StartServiceCtrlDispatcher()
    else:
        win32serviceutil.HandleCommandLine(MyServiceFramework)


if __name__ == '__main__':
    init()