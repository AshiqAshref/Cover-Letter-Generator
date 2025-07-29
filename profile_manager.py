import os
import json
import os
import json
from config import PROFILES_DIR, DEFAULT_PERSONAL_CONTEXT, DEFAULT_SYSTEM_INSTRUCTION_TEMPLATE, DEFAULT_SYSTEM_CORE_RULES, DEFAULT_GEMINI_MODEL

# Create a directory for personal context files
PERSONAL_CONTEXT_DIR = os.path.join(
    os.path.dirname(PROFILES_DIR), 'personal_context')
if not os.path.exists(PERSONAL_CONTEXT_DIR):
    os.makedirs(PERSONAL_CONTEXT_DIR)


class ProfileManager:
    """Manages creation, loading, saving and deletion of user profiles"""

    _instance = None

    def __new__(cls):
        """Implement singleton pattern"""
        if cls._instance is None:
            cls._instance = super(ProfileManager, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        """Initialize the profile manager"""
        if not self._initialized:
            self._current_profile_name = "Default"
            self._current_personal_context = DEFAULT_PERSONAL_CONTEXT
            self._current_system_template = DEFAULT_SYSTEM_INSTRUCTION_TEMPLATE
            # Use default system core rules from config
            self._current_system_core_rules = DEFAULT_SYSTEM_CORE_RULES
            self._current_resume_path = None
            # Store the selected model for the profile
            # Ensure default profile exists
            self._current_model = DEFAULT_GEMINI_MODEL
            if not self.profile_exists("Default"):
                self.save_profile("Default", DEFAULT_PERSONAL_CONTEXT,
                                  DEFAULT_SYSTEM_INSTRUCTION_TEMPLATE,
                                  system_core_rules=DEFAULT_SYSTEM_CORE_RULES)
            else:
                # Load it if it exists
                profile_data = self.load_profile("Default")
                if profile_data:
                    self._current_personal_context = profile_data.get(
                        "personal_context", DEFAULT_PERSONAL_CONTEXT)
                    self._current_system_template = profile_data.get(
                        "system_template", DEFAULT_SYSTEM_INSTRUCTION_TEMPLATE)
                    self._current_system_core_rules = profile_data.get(
                        "system_core_rules", DEFAULT_SYSTEM_CORE_RULES)
                    self._current_resume_path = profile_data.get(
                        "resume_path", None)
                    self._current_model = profile_data.get(
                        "model", DEFAULT_GEMINI_MODEL)

            self._initialized = True

    def _get_personal_context_filepath(self, name):
        """Get the file path for personal context file"""
        return os.path.join(PERSONAL_CONTEXT_DIR, f"{name}.txt")

    def save_profile(self, name, personal_context, system_template, resume_path=None, system_core_rules=None, model=None):
        """Save a profile to a JSON file"""
        # Save personal context to a separate file
        personal_context_filepath = self._get_personal_context_filepath(name)
        with open(personal_context_filepath, 'w', encoding='utf-8') as f:
            # Get current system core rules if not provided
            f.write(personal_context)
        if system_core_rules is None:
            system_core_rules = self._current_system_core_rules

        # Get current model if not provided
        if model is None:
            model = self._current_model

        profile_data = {
            "system_template": system_template,
            "system_core_rules": system_core_rules,
            "resume_path": resume_path,
            "model": model
        }

        file_path = os.path.join(PROFILES_DIR, f"{name}.json")
        with open(file_path, 'w') as f:
            json.dump(profile_data, f, indent=4)

        return True

    def load_profile(self, name):
        """Load a profile from a JSON file"""
        file_path = os.path.join(PROFILES_DIR, f"{name}.json")
        try:
            with open(file_path, 'r') as f:
                profile_data = json.load(f)

            # Load personal context from separate file
            personal_context_filepath = self._get_personal_context_filepath(
                name)
            try:
                with open(personal_context_filepath, 'r', encoding='utf-8') as f:
                    personal_context = f.read()
            except FileNotFoundError:
                # If personal context file doesn't exist, use default
                personal_context = DEFAULT_PERSONAL_CONTEXT

            # Add personal context to the profile data
            profile_data["personal_context"] = personal_context

            # Ensure system_core_rules exists (for backward compatibility)
            if "system_core_rules" not in profile_data:
                profile_data["system_core_rules"] = ""

            return profile_data
        except FileNotFoundError:
            return None

    def delete_profile(self, name):
        """Delete a profile"""
        if name == "Default":
            return False  # Don't allow deletion of Default profile

        file_path = os.path.join(PROFILES_DIR, f"{name}.json")
        personal_context_filepath = self._get_personal_context_filepath(name)

        try:
            # Delete both the profile JSON and personal context file
            os.remove(file_path)
            if os.path.exists(personal_context_filepath):
                os.remove(personal_context_filepath)
            return True
        except Exception as e:
            print(f"Error deleting profile {name}: {str(e)}")
            return False

    def list_profiles(self):
        """List all available profiles"""
        profiles = []
        for file in os.listdir(PROFILES_DIR):
            if file.endswith('.json'):
                profiles.append(os.path.splitext(file)[0])
        return profiles

    def profile_exists(self, name):
        """Check if a profile exists"""
        return os.path.exists(os.path.join(PROFILES_DIR, f"{name}.json"))

    # Getters and setters for current profile information

    @property
    def current_profile_name(self):
        return self._current_profile_name

    @current_profile_name.setter
    def current_profile_name(self, name):
        self._current_profile_name = name

    @property
    def current_personal_context(self):
        return self._current_personal_context

    @current_personal_context.setter
    def current_personal_context(self, context):
        self._current_personal_context = context

    @property
    def current_system_template(self):
        return self._current_system_template

    @current_system_template.setter
    def current_system_template(self, template):
        self._current_system_template = template

    @property
    def current_system_core_rules(self):
        return self._current_system_core_rules

    @current_system_core_rules.setter
    def current_system_core_rules(self, rules):
        self._current_system_core_rules = rules

    @property
    def current_resume_path(self):
        return self._current_resume_path

    @current_resume_path.setter
    def current_resume_path(self, path):
        self._current_resume_path = path

    @property
    def current_model(self):
        return self._current_model

    @current_model.setter
    def current_model(self, model):
        self._current_model = model

    def set_current_profile(self, name):
        """Set the current profile and load its data"""
        if not self.profile_exists(name):
            return False

        profile_data = self.load_profile(name)
        if not profile_data:
            return False

        self._current_profile_name = name
        self._current_personal_context = profile_data.get(
            "personal_context", DEFAULT_PERSONAL_CONTEXT)
        self._current_system_template = profile_data.get(
            "system_template", DEFAULT_SYSTEM_INSTRUCTION_TEMPLATE)
        self._current_system_core_rules = profile_data.get(
            "system_core_rules", "")
        self._current_resume_path = profile_data.get("resume_path", None)
        self._current_model = profile_data.get("model", DEFAULT_GEMINI_MODEL)

        return True

    def update_current_profile(self):
        """Update the current profile file with current data"""
        return self.save_profile(
            self._current_profile_name,
            self._current_personal_context,
            self._current_system_template,
            self._current_resume_path,
            self._current_system_core_rules,
            self._current_model
        )

    def restore_defaults(self):
        """Restore default profile settings"""
        self._current_personal_context = DEFAULT_PERSONAL_CONTEXT
        self._current_system_template = DEFAULT_SYSTEM_INSTRUCTION_TEMPLATE
        self._current_system_core_rules = DEFAULT_SYSTEM_CORE_RULES
        self._current_resume_path = None

    def get_save_folder(self):
        """Retrieve the folder path for saving Word files from the current profile."""
        profile = self.load_profile(self.current_profile_name)
        return profile.get("save_folder", None)

    def set_save_folder(self, folder_path):
        """Set the folder path for saving Word files in the current profile."""
        profile = self.load_profile(self.current_profile_name)
        profile["save_folder"] = folder_path
        file_path = os.path.join(
            PROFILES_DIR, f"{self.current_profile_name}.json")
        with open(file_path, 'w') as f:
            json.dump(profile, f, indent=4)

    def get_save_preferences(self):
        """Get all save preferences related to Word file saving."""
        profile = self.load_profile(self.current_profile_name)
        return {
            "save_folder": profile.get("save_folder", None),
            "always_use_default_folder": profile.get("always_use_default_folder", False),
            "auto_save_as_word": profile.get("auto_save_as_word", False),
            "overwrite_existing_files": profile.get("overwrite_existing_files", False)
        }

    def set_save_preferences(self, always_use_default=None, auto_save=None, overwrite_files=None, save_folder=None):
        """Update save preferences for the current profile."""
        profile = self.load_profile(self.current_profile_name)

        if always_use_default is not None:
            profile["always_use_default_folder"] = always_use_default

        if auto_save is not None:
            profile["auto_save_as_word"] = auto_save

        if overwrite_files is not None:
            profile["overwrite_existing_files"] = overwrite_files

        if save_folder is not None:
            profile["save_folder"] = save_folder

        file_path = os.path.join(
            PROFILES_DIR, f"{self.current_profile_name}.json")
        with open(file_path, 'w') as f:
            json.dump(profile, f, indent=4)
