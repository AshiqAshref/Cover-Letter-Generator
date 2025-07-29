#!/usr/bin/env python3
"""
Script to sign and notarize a macOS application bundle.
Run this on macOS after building with build_mac.py.

Prerequisites:
- Apple Developer account
- Developer ID Application certificate in Keychain
- App-specific password for Apple ID
"""

import os
import subprocess
import sys
import argparse
import time


def run_command(command, description=None):
    """Run a shell command and print its output"""
    if description:
        print(f"\n{description}...")

    try:
        result = subprocess.run(command, shell=True, check=True, text=True,
                                capture_output=True)
        print(result.stdout)
        return result.stdout
    except subprocess.CalledProcessError as e:
        print(f"Error: {e}")
        print(e.stderr)
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(
        description='Sign and notarize a macOS application')
    parser.add_argument('--app_path', default='dist/CoverLetterGenerator.app',
                        help='Path to the .app bundle')
    parser.add_argument('--dev_identity', required=True,
                        help='Developer ID Application certificate identity (e.g., "Developer ID Application: Your Name (TEAM_ID)")')
    parser.add_argument('--apple_id', required=True,
                        help='Apple ID email used for notarization')
    parser.add_argument('--app_password', required=True,
                        help='App-specific password for Apple ID')
    parser.add_argument('--bundle_id', default='com.coverlettergenerator.app',
                        help='Bundle identifier for the application')
    parser.add_argument('--skip_notarization', action='store_true',
                        help='Skip the notarization process')

    args = parser.parse_args()

    # Verify the app exists
    if not os.path.exists(args.app_path):
        print(f"Error: App bundle not found at {args.app_path}")
        sys.exit(1)

    # Step 1: Sign the application
    run_command(
        f'codesign --force --options runtime --deep --sign "{args.dev_identity}" {args.app_path}',
        "Signing application"
    )

    # Step 2: Verify signature
    run_command(
        f'codesign -v --verbose=4 {args.app_path}',
        "Verifying signature"
    )

    # Step 3: Create a DMG
    dmg_name = os.path.basename(args.app_path).replace('.app', '.dmg')
    run_command(
        f'hdiutil create -volname "Cover Letter Generator" -srcfolder {args.app_path} '
        f'-ov -format UDZO "{dmg_name}"',
        "Creating DMG file"
    )

    if args.skip_notarization:
        print("\nSkipping notarization. Your app is signed but not notarized.")
        return

    # Step 4: Notarize the DMG
    print("\nSubmitting app for notarization (this may take several minutes)...")
    notarize_output = run_command(
        f'xcrun altool --notarize-app --primary-bundle-id "{args.bundle_id}" '
        f'--username "{args.apple_id}" --password "{args.app_password}" --file "{dmg_name}"',
        "Submitting for notarization"
    )

    # Extract Request UUID
    import re
    uuid_match = re.search(r'RequestUUID = ([a-f0-9\-]+)', notarize_output)
    if not uuid_match:
        print("Error: Couldn't extract Request UUID from notarization response")
        sys.exit(1)

    request_uuid = uuid_match.group(1)
    print(f"Request UUID: {request_uuid}")

    # Step 5: Wait for notarization to complete
    print("\nWaiting for notarization to complete (checking every 30 seconds)...")
    status = "in progress"
    while status == "in progress":
        time.sleep(30)  # Check every 30 seconds
        status_output = run_command(
            f'xcrun altool --notarization-info {request_uuid} '
            f'--username "{args.apple_id}" --password "{args.app_password}"'
        )

        if "Status: success" in status_output:
            status = "success"
        elif "Status: in progress" in status_output:
            print("Notarization still in progress, waiting...")
        else:
            print(f"Unexpected status: {status_output}")
            status = "failed"

    if status == "success":
        # Step 6: Staple the notarization ticket
        run_command(
            f'xcrun stapler staple "{dmg_name}"',
            "Stapling notarization ticket to DMG"
        )

        # Also staple to the app if possible
        run_command(
            f'xcrun stapler staple "{args.app_path}"',
            "Stapling notarization ticket to app bundle"
        )

        print("\nNotarization complete! Your app is now signed and notarized.")
    else:
        print("\nNotarization failed. Check the logs for details.")


if __name__ == "__main__":
    main()
