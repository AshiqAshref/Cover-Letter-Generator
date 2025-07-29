#!/usr/bin/env python3
# pip install google-genai


"""
Cover Letter Generator Application
---------------------------------
A tool for generating customized cover letters using Google Gemini AI,
with support for profile management and resume context.
"""

import os
import sys
import tkinter as tk

# Add missing import for os in gui.py
from gui import CoverLetterGeneratorApp


def main():
    """Main entry point for the application"""
    app = CoverLetterGeneratorApp()
    app.run()


if __name__ == "__main__":
    main()
