"""
Build script for creating an executable of the Cover Letter Generator.
Run this with: python build_exe.py
"""

import PyInstaller.__main__
import os

# Get the current directory
base_dir = os.path.dirname(os.path.abspath(__file__))

# Define the path to main.py
main_py = os.path.join(base_dir, 'main.py')

# Define paths to data directories that need to be included
profiles_dir = os.path.join(base_dir, 'profiles')
cache_dir = os.path.join(base_dir, 'cache')
files_dir = os.path.join(base_dir, 'files')
personal_context_dir = os.path.join(base_dir, 'personal_context')
chat_states_dir = os.path.join(base_dir, 'chat_states')
settings_file = os.path.join(base_dir, 'settings.json')

# Define the PyInstaller command
PyInstaller.__main__.run([
    main_py,
    '--name=CoverLetterGenerator',
    '--windowed',  # GUI mode (no console)
    '--onefile',   # Create a single executable file
    '--add-data={}{}profiles'.format(profiles_dir, os.pathsep),
    '--add-data={}{}cache'.format(cache_dir, os.pathsep),
    '--add-data={}{}files'.format(files_dir, os.pathsep),
    '--add-data={}{}personal_context'.format(personal_context_dir, os.pathsep),
    '--add-data={}{}chat_states'.format(chat_states_dir, os.pathsep),
    '--add-data={}{}settings.json'.format(settings_file, os.pathsep),
    '--icon=files/storage/icon.ico',  # Optional: Add an icon if you have one
    '--clean',  # Clean PyInstaller cache
    '--noconfirm',  # Replace output directory without asking
])
