import os
from google import genai
from google.genai import types
from pydantic import TypeAdapter
import hashlib
import io

from config import GEMINI_API_KEY
from local_storage_manager import LocalStorageManager
from cache_manager import CacheManager
from profile_manager import ProfileManager, PERSONAL_CONTEXT_DIR


CHAT_STATE_DIR = os.path.join(os.path.dirname(
    PERSONAL_CONTEXT_DIR), 'chat_states')  # Directory for chat state storage
if not os.path.exists(CHAT_STATE_DIR):
    os.makedirs(CHAT_STATE_DIR)


class GeminiClient:
    """Handles all interactions with the Gemini API"""

    _instance = None

    def __new__(cls):
        """Implement singleton pattern"""
        if cls._instance is None:
            cls._instance = super(GeminiClient, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        """Initialize the Gemini API client"""
        if not self._initialized:
            self.profile_manager = ProfileManager()
            self.api_key = GEMINI_API_KEY

            if not self.api_key:
                print("API key is missing! Please add an API key in the settings.")
                self.api_key = None  # Allow initialization to proceed without crashing

            self.model = self.profile_manager.current_model
            self.client = genai.Client(
                api_key=self.api_key) if self.api_key else None
            self.storage_manager = LocalStorageManager()
            self.cache_manager = CacheManager()
            # TypeAdapter for chat history serialization
            self.history_adapter = TypeAdapter(list[types.Content])

            self.chat_sessions = {}  # Dictionary to store chat sessions by profile hash
            self._initialized = True

    def _get_profile_hash(self, profile_name, system_template, system_core_rules, resume_path=None):
        """Generate a unique hash for the profile and resume combination"""

        # Get the personal context file path
        personal_context_file = os.path.join(
            PERSONAL_CONTEXT_DIR, f"{profile_name}.txt")
        # Combine system template, core rules, and profile name for hashing
        content = system_template + system_core_rules + profile_name

        # Add hash of the personal context file if it exists
        if os.path.exists(personal_context_file):
            try:
                with open(personal_context_file, 'rb') as f:
                    file_content = f.read()
                    file_hash = hashlib.md5(file_content).hexdigest()[:8]
                    content += file_hash
            except Exception as e:
                print(f"Error hashing personal context file: {str(e)}")
        # Add resume hash to ensure different resumes create different sessions
        if resume_path and os.path.exists(resume_path):
            try:
                with open(resume_path, 'rb') as f:
                    resume_content = f.read()
                    resume_hash = hashlib.md5(resume_content).hexdigest()[:8]
                    content += resume_hash
            except Exception as e:
                print(f"Error hashing resume file: {str(e)}")

        return hashlib.md5(content.encode()).hexdigest()

    def _get_chat_state_filepath(self, profile_hash):
        """Get the filepath for saving chat state"""
        return os.path.join(CHAT_STATE_DIR, f"{profile_hash}.json")

    def _save_chat_state(self, profile_hash, chat):
        """Save chat state to a file for later retrieval"""
        try:
            chat_history = chat.get_history()
            # Only save if we have a successful initialization (at least 2 messages)
            if len(chat_history) >= 2:
                # Convert to a JSON list using the TypeAdapter
                json_history = self.history_adapter.dump_json(chat_history)
                filepath = self._get_chat_state_filepath(
                    profile_hash)  # Save to a file
                with open(filepath, 'wb') as f:
                    f.write(json_history)

                print(f"Chat state saved for profile: {profile_hash[:8]}")
                return True
        except Exception as e:
            print(f"Error saving chat state: {str(e)}")

        return False

    def _load_chat_state(self, profile_hash, system_template, system_core_rules):
        """Load chat state from file if available"""
        filepath = self._get_chat_state_filepath(profile_hash)

        try:
            if os.path.exists(filepath):
                with open(filepath, 'rb') as f:
                    json_history = f.read()

                # Convert the JSON back to the Pydantic schema
                history = self.history_adapter.validate_json(json_history)
                combined_system_instructions = system_template + system_core_rules

                chat = self.client.chats.create(
                    model=self.model,
                    config=types.GenerateContentConfig(
                        system_instruction=combined_system_instructions
                    ),
                    history=history,
                )

                print(f"Chat state loaded for profile: {profile_hash[:8]}")
                return chat
        except Exception as e:
            print(f"Error loading chat state: {str(e)}")

        return None

    def _initialize_chat_session(self, system_template, system_core_rules, resume_path=None):
        """Initialize a chat session with context from personal profile and resume"""
        profile_name = self.profile_manager.current_profile_name  # Get the current profile name to identify the personal context file
        profile_hash = self._get_profile_hash(
            profile_name, system_template, system_core_rules, resume_path)

        # Try to load existing chat state from file
        chat = self._load_chat_state(
            profile_hash, system_template, system_core_rules)
        if chat:
            print(f"Using saved initial state for profile: {profile_hash[:8]}")
            return chat, profile_hash
        print(f"Creating new chat session for profile: {profile_hash[:8]}")

        combined_system_instructions = system_template + system_core_rules
        print("\n\n=================================Combined System Instructions=================================")
        print(f"Combined system instructions: {combined_system_instructions}")
        print("=================================Combined System Instructions=================================\n\n\n")

        chat = self.client.chats.create(  # Create a new chat session if loading failed
            model=self.model,
            config=types.GenerateContentConfig(
                system_instruction=combined_system_instructions
            ),
        )

        personal_context_file = os.path.join(
            # Get personal context from file
            PERSONAL_CONTEXT_DIR, f"{profile_name}.txt")
        context_message = f"sending info"
        files_to_send = []

        # Add personal context file if it exists
        if os.path.exists(personal_context_file):
            try:
                with open(personal_context_file, 'rb') as file:
                    personal_context_io = io.BytesIO(file.read())
                personal_context_file_obj = self.client.files.upload(
                    file=personal_context_io,
                    config=dict(mime_type='text/plain')
                )
                files_to_send.append(personal_context_file_obj)
                print(
                    f"Personal context file attached: {personal_context_file}")
            except Exception as e:
                print(f"Error attaching personal context file: {str(e)}")

        # Add resume content if available
        if resume_path and os.path.exists(resume_path) and resume_path.lower().endswith('.pdf'):
            try:
                with open(resume_path, 'rb') as file:
                    doc_io = io.BytesIO(file.read())
                sample_pdf = self.client.files.upload(
                    file=doc_io,
                    config=dict(mime_type='application/pdf')
                )
                files_to_send.append(sample_pdf)
                print(f"Resume file attached: {resume_path}")
            except Exception as e:
                print(f"Error attaching resume file: {str(e)}")

        try:  # Send the context message and files to the chat
            if files_to_send:
                response = chat.send_message(
                    message=[context_message] + files_to_send
                )
            else:
                response = chat.send_message(context_message)

            print(f"Response from AI: {response.text}")
            print(f"sent files: {files_to_send}")
            print("Profile context loaded into chat session")

            # This is the state we'll return to after each generation
            self._save_chat_state(profile_hash, chat)

        except Exception as e:
            print(f"Error sending files to chat: {str(e)}")
            # Fallback to just sending text
            response = chat.send_message(context_message)
            print(f"Response from AI: {response.text}")

        return chat, profile_hash

    def generate_cover_letter(self, job_description, personal_context, system_template, update_ui_callback=None):
        """
        Generate a cover letter using chat-based context

        Args:
            job_description: The job description text
            personal_context: The user's personal context
            system_template: The system instruction template
            update_ui_callback: Optional callback function to update UI with streaming responses

        Returns:
            The generated cover letter text
        """
        try:
            # Get system core rules from the profile manager
            system_core_rules = self.profile_manager.current_system_core_rules
            chat, profile_hash = self._initialize_chat_session(
                system_template, system_core_rules)

            if update_ui_callback:
                stream_response = chat.send_message_stream(
                    # Stream the response to the UI
                    message=[job_description, system_core_rules])
                cover_letter = ""

                for chunk in stream_response:
                    if chunk.text:
                        cover_letter += chunk.text
                        # Update the UI with the current text
                        update_ui_callback(cover_letter)
                return cover_letter
            else:  # Non-streaming version (original behavior)
                response = chat.send_message(
                    message=[job_description, system_core_rules])
                return response.text

        except Exception as e:
            print(f"Error generating cover letter with chat: {str(e)}")

            system_instruction = system_template.format(
                personal_context=personal_context)
            system_instruction += self.profile_manager.current_system_core_rules

            try:  # Make direct API call without chat history
                response = self.client.models.generate_content(
                    model=self.model,
                    contents=[job_description, system_core_rules],
                    config=types.GenerateContentConfig(
                        system_instruction=system_instruction,
                        response_mime_type="text/plain",
                    )
                )
                return response.text
            except Exception as fallback_error:
                print(f"Error in fallback generation: {str(fallback_error)}")
                return f"Error generating cover letter: {str(e)}\nFallback error: {str(fallback_error)}"

    def generate_cover_letter_with_files(self, job_description, personal_context, system_template, resume_path=None, update_ui_callback=None):
        """
        Generate a cover letter using chat-based context with resume

        Args:
            job_description: The job description text
            personal_context: The user's personal context
            system_template: The system instruction template
            resume_path: Path to a resume PDF file
            update_ui_callback: Optional callback function to update UI with streaming responses

        Returns:
            The generated cover letter text
        """
        try:
            system_core_rules = self.profile_manager.current_system_core_rules
            chat, profile_hash = self._initialize_chat_session(
                system_template, system_core_rules, resume_path)

            if update_ui_callback:
                stream_response = chat.send_message_stream(
                    # Stream the response to the UI
                    message=[job_description, system_core_rules])
                cover_letter = ""

                for chunk in stream_response:  # Process each chunk as it arrives
                    if chunk.text:
                        cover_letter += chunk.text
                        # Update the UI with the current text
                        update_ui_callback(cover_letter)
                return cover_letter
            else:  # Non-streaming version (original behavior)
                response = chat.send_message(
                    message=[job_description, system_core_rules])
                return response.text

        except Exception as e:
            print(
                f"Error generating cover letter with chat and files: {str(e)}")
            # Fall back to the standard approach without chat
            return self.generate_cover_letter(job_description, personal_context, system_template, update_ui_callback)

    def clear_chats(self):
        """Clear all chat sessions from memory and storage"""
        self.chat_sessions = {}

        try:  # Also delete saved chat states
            for file in os.listdir(CHAT_STATE_DIR):
                if file.endswith('.json'):
                    os.remove(os.path.join(CHAT_STATE_DIR, file))
            print("All saved chat states cleared")
        except Exception as e:
            print(f"Error clearing chat state files: {str(e)}")

        return True

    def update_api_key(self, new_key):
        """Update the API key and reinitialize the client"""
        try:
            self.api_key = new_key
            self.client = genai.Client(api_key=self.api_key)
            print("API key updated successfully.")
            return True
        except Exception as e:
            print(f"Error updating API key: {str(e)}")
            return False

    def update_model(self, new_model):
        """Update the model being used"""
        self.model = new_model
        # Clear chat sessions to ensure the new model is used
        self.chat_sessions = {}
