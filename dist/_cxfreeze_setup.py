import sys
import os
from cx_Freeze import setup, Executable

sys_python_path = os.path.dirname(sys.executable)

# Dependencies are automatically detected, but it might need fine tuning.
build_exe_options = {
	"packages": ["cherrypy"],
	"includes": ["cherrypy.wsgiserver", "cherrypy.wsgiserver.wsgiserver3"],
	"excludes": ["tkinter",],
}

scriptPath = os.path.normpath(os.path.join(os.path.dirname(os.path.realpath(sys.argv[0])), "csfrd"))

sys.path.insert(0, scriptPath)
path = sys.path

base = None
setup(  name = "csfrd",
        version = "0.1",
        description = "SFRDirect Daemon",
        options = {"build_exe": build_exe_options},
        executables = [Executable(os.path.join(scriptPath, "csfrd.py"), base=base)])