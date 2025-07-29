import os
import shutil
import uuid
import hashlib
from config import FILES_DIR


class LocalStorageManager:
    """Manages file storage operations locally instead of using Firebase"""

    _instance = None

    def __new__(cls):
        """Implement singleton pattern"""
        if cls._instance is None:
            cls._instance = super(LocalStorageManager, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        """Initialize the local storage manager"""
        if not self._initialized:
            self.initialized = True
            self.local_storage_dir = os.path.join(FILES_DIR, "storage")
            # Create storage directory if it doesn't exist
            if not os.path.exists(self.local_storage_dir):
                os.makedirs(self.local_storage_dir)
            self._initialized = True

    def upload_file(self, file_path, destination_path=None):
        """
        Copy a file to local storage and return the local path

        Args:
            file_path: Local path to the file to be copied
            destination_path: Optional destination path (if None, generates a unique name)

        Returns:
            The local path to the copied file, or None if copy failed
        """
        try:
            # Generate a unique filename if destination_path not provided
            if not destination_path:
                file_extension = os.path.splitext(file_path)[1]
                unique_id = str(uuid.uuid4())
                destination_path = f"resumes/{unique_id}{file_extension}"

            # Ensure the destination directory exists
            dest_dir = os.path.join(
                self.local_storage_dir, os.path.dirname(destination_path))
            if not os.path.exists(dest_dir):
                os.makedirs(dest_dir)

            # Full path for the destination file
            dest_file_path = os.path.join(
                self.local_storage_dir, destination_path)

            # Copy the file
            shutil.copy2(file_path, dest_file_path)

            # Return the local path (this replaces the public URL concept from Firebase)
            return dest_file_path
        except Exception as e:
            print(f"Error copying file to local storage: {str(e)}")
            return None

    def save_text_to_file(self, text_content, file_name=None, subdirectory="profiles"):
        """
        Save text content to a file in the local storage

        Args:
            text_content: The text content to save to file
            file_name: Optional file name (if None, generates a name based on content hash)
            subdirectory: Optional subdirectory within the storage directory (default: "profiles")

        Returns:
            The local path to the saved file, or None if save failed
        """
        try:
            # Generate a filename if not provided
            if file_name is None:
                # Create a short hash of the content for the filename
                content_hash = hashlib.md5(
                    text_content.encode()).hexdigest()[:8]
                file_name = f"personal_context_{content_hash}.txt"

            # Ensure the subdirectory exists
            dest_dir = os.path.join(self.local_storage_dir, subdirectory)
            if not os.path.exists(dest_dir):
                os.makedirs(dest_dir)

            # Full path for the destination file
            dest_file_path = os.path.join(dest_dir, file_name)

            # Write the content to the file
            with open(dest_file_path, 'w', encoding='utf-8') as file:
                file.write(text_content)

            print(f"Text content saved to: {dest_file_path}")
            return dest_file_path
        except Exception as e:
            print(f"Error saving text content to file: {str(e)}")
            return None

    def is_available(self):
        """Check if local storage is available"""
        return self.initialized and os.path.exists(self.local_storage_dir)
