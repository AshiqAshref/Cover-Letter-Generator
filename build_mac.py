#!/usr/bin/env python3
"""
Build script for creating a macOS executable (.app) of the Cover Letter Generator.
Run this with: python build_mac.py
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

# Define the PyInstaller command with macOS specific options
PyInstaller.__main__.run([
    main_py,
    '--name=CoverLetterGenerator',
    '--windowed',     # Creates a .app bundle for macOS
    '--onedir',       # Creates a single folder with the app bundle instead of onefile
    '--add-data={}{}profiles'.format(profiles_dir, os.pathsep),
    '--add-data={}{}cache'.format(cache_dir, os.pathsep),
    '--add-data={}{}files'.format(files_dir, os.pathsep),
    '--add-data={}{}personal_context'.format(personal_context_dir, os.pathsep),
    '--add-data={}{}chat_states'.format(chat_states_dir, os.pathsep),
    '--add-data={}{}settings.json'.format(settings_file, os.pathsep),
    # PyInstaller will convert .ico to .icns for macOS
    '--icon=files/storage/icon.ico',
    # Bundle identifier for macOS
    '--osx-bundle-identifier=com.coverlettergenerator.app',
    '--target-architecture=universal2',  # Build for both Intel and Apple Silicon
    '--clean',        # Clean PyInstaller cache
    '--noconfirm',    # Replace output directory without asking
])

print("Build complete! Your macOS app can be found in the dist directory.")
print("Note: To make this distributable, you may need to sign the app with a Developer ID.")
