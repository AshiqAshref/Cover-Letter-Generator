import tkinter as tk
from tkinter import scrolledtext, ttk, messagebox, simpledialog, filedialog
import threading
import os
import tkinter.filedialog as filedialog
from docx import Document

from profile_manager import ProfileManager
from gemini_client import GeminiClient
from config import GEMINI_API_KEY, DEFAULT_GEMINI_MODEL, load_settings, save_settings


class TabBase:
    """Base class for all tabs in the application"""

    def __init__(self, parent):
        """Initialize the tab"""
        self.parent = parent
        self.frame = ttk.Frame(parent)

    def get_frame(self):
        """Get the frame for this tab"""
        return self.frame

    def update(self):
        """Update the tab contents - override in subclasses"""
        pass

    def _add_context_menu(self, widget):
        """Add right-click context menu to a widget"""
        if isinstance(widget, (tk.Entry, tk.Text, scrolledtext.ScrolledText)):
            # Create context menu
            context_menu = tk.Menu(widget, tearoff=0)
            context_menu.add_command(
                label="Cut", command=lambda: self._handle_context_menu_action(widget, "cut"))
            context_menu.add_command(
                label="Copy", command=lambda: self._handle_context_menu_action(widget, "copy"))
            context_menu.add_command(
                label="Paste", command=lambda: self._handle_context_menu_action(widget, "paste"))
            context_menu.add_separator()
            context_menu.add_command(
                label="Select All", command=lambda: self._handle_context_menu_action(widget, "select_all"))

            # Bind right-click event
            widget.bind("<Button-3>", lambda event,
                        menu=context_menu: self._show_context_menu(event, menu))

            # Enable text selection
            widget.configure(state=tk.NORMAL)

            # Make ScrolledText selectable even when disabled
            if isinstance(widget, scrolledtext.ScrolledText):
                widget.bind("<1>", lambda event: widget.focus_set())

    def _show_context_menu(self, event, menu):
        """Show the context menu at mouse position"""
        try:
            menu.tk_popup(event.x_root, event.y_root)
        finally:
            menu.grab_release()

    def _handle_context_menu_action(self, widget, action):
        """Handle context menu actions"""
        if action == "cut":
            widget.event_generate("<<Cut>>")
        elif action == "copy":
            widget.event_generate("<<Copy>>")
        elif action == "paste":
            widget.event_generate("<<Paste>>")
        elif action == "select_all":
            # Select all text in the widget
            if isinstance(widget, (tk.Text, scrolledtext.ScrolledText)):
                widget.tag_add(tk.SEL, "1.0", tk.END)
                widget.mark_set(tk.INSERT, "1.0")
                widget.see(tk.INSERT)
                return "break"  # Prevent default behavior
            elif isinstance(widget, tk.Entry):
                widget.select_range(0, tk.END)
                widget.icursor(tk.END)

    def _make_readonly_selectable(self, widget):
        """Make a read-only text widget selectable for copying"""
        if isinstance(widget, (tk.Text, scrolledtext.ScrolledText)):
            # Allow selection even when readonly
            widget.bind("<Button-1>", lambda event: widget.focus_set())
            # Right-click context menu with only copy
            context_menu = tk.Menu(widget, tearoff=0)
            context_menu.add_command(
                label="Copy", command=lambda: widget.event_generate("<<Copy>>"))
            context_menu.add_command(
                label="Select All", command=lambda: self._select_all_text(widget))
            widget.bind("<Button-3>", lambda event,
                        menu=context_menu: self._show_context_menu(event, menu))

    def _select_all_text(self, widget):
        """Select all text in a widget"""
        if isinstance(widget, (tk.Text, scrolledtext.ScrolledText)):
            widget.tag_add(tk.SEL, "1.0", tk.END)
            widget.mark_set(tk.INSERT, "1.0")
            widget.see(tk.INSERT)
            return "break"  # Prevent default behavior

    def _add_listbox_context_menu(self, listbox):
        """Add right-click context menu specifically for Listbox widgets"""
        context_menu = tk.Menu(listbox, tearoff=0)
        context_menu.add_command(
            label="Copy", command=lambda: self._copy_listbox_selection(listbox))

        # Bind right-click event
        listbox.bind("<Button-3>", lambda event,
                     menu=context_menu: self._show_context_menu(event, menu))

    def _copy_listbox_selection(self, listbox):
        """Copy selected item from listbox to clipboard"""
        selected_indices = listbox.curselection()
        if selected_indices:
            selected_index = selected_indices[0]
            selected_text = listbox.get(selected_index)
            self.parent.master.clipboard_clear()
            self.parent.master.clipboard_append(selected_text)


class MainTab(TabBase):
    """Tab for generating cover letters"""

    def __init__(self, parent, app):
        """Initialize the main tab"""
        super().__init__(parent)
        self.app = app
        self.profile_manager = ProfileManager()
        self.gemini_client = GeminiClient()

        # Create frames for input and output
        self.input_frame = tk.Frame(self.frame, padx=10, pady=10)
        self.input_frame.pack(fill=tk.BOTH, expand=True)

        # Profile indicator
        self.profile_indicator_frame = tk.Frame(self.input_frame)
        self.profile_indicator_frame.pack(fill=tk.X, pady=5)

        tk.Label(self.profile_indicator_frame, text="Current Profile:",
                 font=("Arial", 10, "bold")).pack(side=tk.LEFT, padx=(0, 5))
        self.current_profile_label = tk.Label(
            self.profile_indicator_frame, text=self.profile_manager.current_profile_name, font=("Arial", 10), fg="#2196F3")
        self.current_profile_label.pack(side=tk.LEFT)

        # Add resume file indicator
        tk.Label(self.profile_indicator_frame, text=" | Resume:", font=(
            "Arial", 10, "bold")).pack(side=tk.LEFT, padx=(20, 5))
        self.resume_indicator = tk.Label(
            self.profile_indicator_frame, text="None", font=("Arial", 10), fg="#f44336")
        # Job description input and warning frame
        self.resume_indicator.pack(side=tk.LEFT)
        self.job_desc_header_frame = tk.Frame(self.input_frame)
        self.job_desc_header_frame.pack(fill=tk.X, pady=(10, 5))

        tk.Label(self.job_desc_header_frame, text="Job Description:", font=(
            "Arial", 12, "bold")).pack(side=tk.LEFT)

        # Warning label (initially hidden)
        self.job_desc_warning = tk.Label(self.job_desc_header_frame, text="Please enter a job description",
                                         fg="#FF9800", font=("Arial", 10, "italic"))

        self.job_desc_input = scrolledtext.ScrolledText(
            self.input_frame, height=10, width=80, wrap=tk.WORD, font=("Arial", 10))
        self.job_desc_input.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        self._add_context_menu(self.job_desc_input)

        # Resume selection
        self.resume_selection_frame = tk.Frame(self.input_frame)
        self.resume_selection_frame.pack(fill=tk.X, pady=5)

        tk.Label(self.resume_selection_frame, text="Resume for this job:", font=(
            "Arial", 10, "bold")).pack(side=tk.LEFT, padx=(0, 5))

        # Resume options
        self.resume_option_var = tk.StringVar(value="profile")

        self.profile_resume_radio = tk.Radiobutton(
            self.resume_selection_frame, text="Use profile resume", variable=self.resume_option_var, value="profile")
        self.profile_resume_radio.pack(side=tk.LEFT, padx=(0, 10))

        self.custom_resume_radio = tk.Radiobutton(self.resume_selection_frame, text="Custom resume for this job",
                                                  variable=self.resume_option_var, value="custom")
        self.custom_resume_radio.pack(side=tk.LEFT)

        # Custom resume path for this job
        self.custom_resume_frame = tk.Frame(self.input_frame)
        self.custom_resume_frame.pack(fill=tk.X, pady=(0, 5))

        self.custom_resume_path_var = tk.StringVar()
        self.custom_resume_entry = tk.Entry(
            self.custom_resume_frame, textvariable=self.custom_resume_path_var, width=60)
        self.custom_resume_entry.pack(
            side=tk.LEFT, padx=(20, 5), fill=tk.X, expand=True)
        self._add_context_menu(self.custom_resume_entry)

        # Initially hide the custom resume entry
        self.custom_resume_frame.pack_forget()

        # Add trace to the resume option variable
        self.resume_option_var.trace_add("write", self._toggle_custom_resume)
        # Browse button for custom resume
        self.browse_custom_button = tk.Button(self.custom_resume_frame, text="Browse...",
                                              command=self._browse_custom_resume, bg="#2196F3", fg="white", font=("Arial", 10))
        self.browse_custom_button.pack(side=tk.LEFT, padx=5)
        # Generate button and status frame
        generate_frame = tk.Frame(self.input_frame)
        generate_frame.pack(fill=tk.X, pady=10)

        self.generate_button = tk.Button(generate_frame, text="Generate Cover Letter",
                                         command=self._on_generate, bg="#4CAF50", fg="white", font=("Arial", 12, "bold"), height=2)
        self.generate_button.pack(side=tk.LEFT)

        # Status label for generation and file operations
        self.status_label = tk.Label(generate_frame, text="Ready", font=(
            "Arial", 10, "bold"), padx=10, fg="#4CAF50")
        self.status_label.pack(side=tk.LEFT, padx=10, fill=tk.X, expand=True)

        # Output frame
        self.output_frame = tk.Frame(self.frame, padx=10, pady=10)
        self.output_frame.pack(fill=tk.BOTH, expand=True)        # Output
        tk.Label(self.output_frame, text="Generated Cover Letter:",
                 font=("Arial", 12, "bold")).pack(anchor="w")
        self.output_text = scrolledtext.ScrolledText(
            self.output_frame, height=15, width=80, wrap=tk.WORD, font=("Arial", 10))
        self.output_text.pack(fill=tk.BOTH, expand=True, pady=(5, 10))
        # Make text editable (not disabled)
        self._add_context_menu(self.output_text)

        # Button frame with copy button and status message
        self.button_frame = tk.Frame(self.output_frame)
        self.button_frame.pack(fill=tk.X, pady=5)

        # Copy button
        self.copy_button = tk.Button(self.button_frame, text="Copy to Clipboard",
                                     command=self._copy_to_clipboard, bg="#2196F3", fg="white", font=("Arial", 11))
        self.copy_button.pack(side=tk.LEFT, pady=5)

        # Copy status message
        self.copy_status = tk.Label(
            self.button_frame, text="", fg="#4CAF50", font=("Arial", 10, "italic"))
        self.copy_status.pack(side=tk.LEFT, padx=10)

        # Update resume indicator on init
        self.update_resume_indicator()

        # Add save button
        self.add_save_button()

    def _toggle_custom_resume(self, *args):
        """Show or hide custom resume entry based on selection"""
        if self.resume_option_var.get() == "custom":
            self.custom_resume_frame.pack(fill=tk.X, pady=(0, 5))
        else:
            self.custom_resume_frame.pack_forget()

    def _browse_custom_resume(self):
        """Browse for custom resume file"""
        file_path = filedialog.askopenfilename(
            title="Select Resume PDF",
            filetypes=[("PDF Files", "*.pdf"), ("All Files", "*.*")]
        )
        if file_path:
            self.custom_resume_path_var.set(file_path)

    def _copy_to_clipboard(self):
        """Copy output text to clipboard"""
        self.app.root.clipboard_clear()
        self.app.root.clipboard_append(self.output_text.get("1.0", tk.END))
        self.copy_status.config(text="Cover letter copied to clipboard!")
        self.app.root.after(2000, lambda: self.copy_status.config(text=""))

    def update_resume_indicator(self):
        """Update the resume indicator based on current profile"""
        resume_path = self.profile_manager.current_resume_path
        if resume_path and os.path.exists(resume_path):
            self.resume_indicator.config(
                text=os.path.basename(resume_path), fg="#4CAF50")
        else:
            self.resume_indicator.config(text="None", fg="#f44336")

    def update(self):
        """Update the tab when profile changes"""
        self.current_profile_label.config(
            text=self.profile_manager.current_profile_name)
        self.update_resume_indicator()

    def _on_generate(self):
        """Handle generate button click"""
        job_description = self.job_desc_input.get("1.0", tk.END)

        if not job_description.strip():
            # Show inline warning instead of messagebox
            self.job_desc_warning.pack(side=tk.LEFT, padx=10)
            self.app.root.after(
                3000, lambda: self.job_desc_warning.pack_forget())
            return

        # Get resume path if available
        resume_path = None
        if self.resume_option_var.get() == "profile":
            resume_path = self.profile_manager.current_resume_path
        elif self.resume_option_var.get() == "custom":
            custom_path = self.custom_resume_path_var.get().strip()
            if custom_path and os.path.exists(custom_path):
                resume_path = custom_path
        # Generate the cover letter directly
        self._generate_cover_letter(job_description, resume_path)

    def _generate_cover_letter(self, job_description, resume_path=None):
        """Generate the cover letter after confirmation"""
        # Show generating message
        self.output_text.config(state=tk.NORMAL)
        self.output_text.delete("1.0", tk.END)
        self.output_text.insert(
            tk.END, "Generating cover letter...\n\nThis may take a moment. Please wait...")
        self.output_text.config(state=tk.DISABLED)
        self.app.root.update()
        # Update status label
        self.status_label.config(
            text="Generating cover letter...", fg="#FF9800")
        self.app.root.update()

        # Disable generate button during generation
        # Create a callback function to update the UI with streaming responses
        self.generate_button.config(state=tk.DISABLED)

        def update_ui_with_chunk(text):
            self.output_text.config(state=tk.NORMAL)
            self.output_text.delete("1.0", tk.END)
            self.output_text.insert(tk.END, text)
            # Don't disable the text widget so user can edit
            self.app.root.update()  # Use a thread to prevent GUI freezing

        def generate_in_thread():
            try:
                # Get the current profile data
                personal_context = self.profile_manager.current_personal_context
                system_template = self.profile_manager.current_system_template

                # Use the multimodal approach with resume file if available
                cover_letter = self.gemini_client.generate_cover_letter_with_files(
                    job_description, personal_context, system_template, resume_path,
                    update_ui_callback=update_ui_with_chunk
                )

                # No need to update UI here as it's done by the callback during streaming
                # Update status to show generation is complete
                self.app.root.after(0, lambda: self.status_label.config(
                    text="Cover letter generated successfully!", fg="#4CAF50"))

                # Auto-save to Word if enabled in preferences
                save_prefs = self.profile_manager.get_save_preferences()
                if save_prefs.get("auto_save_as_word", False) and cover_letter:
                    self.app.root.after(
                        100, lambda: self.save_to_word(cover_letter))
            except Exception as e:
                error_message = f"Error generating cover letter: {str(e)}"
                self.app.root.after(0, lambda: self._update_output(
                    error_message, is_error=True))
                self.app.root.after(0, lambda: self.status_label.config(
                    text="Generation failed! See error details above.", fg="#f44336"))
            finally:
                # Re-enable the generate button
                self.app.root.after(
                    # Start the generation thread
                    0, lambda: self.generate_button.config(state=tk.NORMAL))
        thread = threading.Thread(target=generate_in_thread)
        thread.daemon = True
        thread.start()

    def _update_output(self, text, is_error=False):
        """Update the output text area with generated content or error"""
        self.output_text.delete("1.0", tk.END)
        self.output_text.insert(tk.END, text)
        # If it's an error, change text color to red
        if is_error:
            self.output_text.tag_configure("error", foreground="red")
            self.output_text.tag_add("error", "1.0", tk.END)

    def save_to_word(self, content):
        """Save the generated content to a Word file."""
        # Get save preferences from the profile manager
        save_prefs = self.profile_manager.get_save_preferences()
        always_use_default = save_prefs.get("always_use_default_folder", False)
        overwrite_existing = save_prefs.get("overwrite_existing_files", False)
        # Determine save folder
        if always_use_default and save_prefs.get("save_folder"):
            save_folder = save_prefs.get("save_folder")
        else:
            save_folder = filedialog.askdirectory(
                title="Select Folder to Save Word File")

        if not save_folder:
            self.status_label.config(
                text="Error: No folder selected for saving!", fg="#f44336")
            return

        default_filename = "CoverLetter.docx"
        filepath = os.path.join(save_folder, default_filename)

        # Handle file naming logic based on preferences
        if os.path.exists(filepath) and not overwrite_existing:
            base_name, ext = os.path.splitext(default_filename)
            counter = 1
            while os.path.exists(filepath):
                filepath = os.path.join(
                    save_folder, f"{base_name}_{counter}{ext}")
                counter += 1

        try:
            doc = Document()
            doc.add_paragraph(content)
            doc.save(filepath)
            self.status_label.config(
                text=f"File saved to: {filepath}", fg="#4CAF50")
            # Don't automatically clear the status - keep it visible
        except Exception as e:
            self.status_label.config(
                text=f"Error: Failed to save file: {str(e)}", fg="#f44336")

    def add_save_button(self):
        """Add a button to save the generated content to a Word file."""
        save_button = tk.Button(self.input_frame, text="Save to Word", command=lambda: self.save_to_word(
            self.output_text.get("1.0", tk.END)))
        save_button.pack(side=tk.LEFT, padx=(10, 0))


class ProfileTab(TabBase):
    """Tab for managing personal profile information"""

    def __init__(self, parent, app):
        """Initialize the profile tab"""
        super().__init__(parent)
        self.app = app
        self.profile_manager = ProfileManager()

        # Personal context editor
        tk.Label(self.frame, text="Personal Profile Information:", font=(
            "Arial", 12, "bold")).pack(anchor="w", padx=10, pady=(10, 5))
        tk.Label(self.frame, text="This information will be used to personalize your cover letters",
                 font=("Arial", 10, "italic")).pack(anchor="w", padx=10, pady=(0, 5))

        # Personal context editor
        self.personal_context_input = scrolledtext.ScrolledText(
            self.frame, height=20, width=80, wrap=tk.WORD, font=("Arial", 10))
        self.personal_context_input.pack(
            fill=tk.BOTH, expand=True, padx=10, pady=5)
        self.personal_context_input.insert(
            tk.END, self.profile_manager.current_personal_context)
        self._add_context_menu(self.personal_context_input)

        # Buttons frame
        profile_buttons_frame = tk.Frame(self.frame, padx=10)
        profile_buttons_frame.pack(fill=tk.X, pady=5)

        save_button = tk.Button(profile_buttons_frame, text="Apply Changes",
                                command=self._save_personal_context, bg="#4CAF50", fg="white", font=("Arial", 11))
        save_button.pack(side=tk.LEFT, padx=5)

        reset_button = tk.Button(profile_buttons_frame, text="Reset to Default",
                                 command=self._reset_personal_context, bg="#f44336", fg="white", font=("Arial", 11))
        reset_button.pack(side=tk.LEFT, padx=5)

        self.save_status_label = tk.Label(
            self.frame, text="", font=("Arial", 10, "italic"), fg="#4CAF50")
        self.save_status_label.pack(pady=5)

        # Add resume upload functionality
        resume_frame = tk.Frame(self.frame, padx=10)
        resume_frame.pack(fill=tk.X, pady=10)

        tk.Label(resume_frame, text="Resume (PDF):", font=(
            "Arial", 11, "bold")).pack(anchor="w", pady=5)

        self.resume_path_var = tk.StringVar()
        resume_path_entry = tk.Entry(
            resume_frame, textvariable=self.resume_path_var, width=60)
        resume_path_entry.pack(side=tk.LEFT, padx=(0, 5),
                               fill=tk.X, expand=True)
        self._add_context_menu(resume_path_entry)

        browse_button = tk.Button(resume_frame, text="Browse...", command=self._browse_resume,
                                  bg="#2196F3", fg="white", font=("Arial", 10))
        browse_button.pack(side=tk.LEFT, padx=5)

        remove_button = tk.Button(resume_frame, text="Remove", command=self._remove_resume,
                                  bg="#f44336", fg="white", font=("Arial", 10))
        remove_button.pack(side=tk.LEFT, padx=5)

        # Update resume path
        self._update_resume_path()

    def _save_personal_context(self):
        """Save changes to personal context"""
        self.profile_manager.current_personal_context = self.personal_context_input.get(
            "1.0", tk.END)
        self.profile_manager.update_current_profile()

        self.save_status_label.config(
            text=f"Profile saved successfully! Changes applied to '{self.profile_manager.current_profile_name}' profile.")
        self.app.root.after(
            2000, lambda: self.save_status_label.config(text=""))

    def _reset_personal_context(self):
        """Reset personal context to default"""
        from config import DEFAULT_PERSONAL_CONTEXT
        self.personal_context_input.delete("1.0", tk.END)
        self.personal_context_input.insert(tk.END, DEFAULT_PERSONAL_CONTEXT)
        self.save_status_label.config(text="Profile reset to default")
        self.app.root.after(
            2000, lambda: self.save_status_label.config(text=""))

    def _browse_resume(self):
        """Browse for resume file"""
        file_path = filedialog.askopenfilename(
            title="Select Resume PDF",
            filetypes=[("PDF Files", "*.pdf"), ("All Files", "*.*")]
        )
        if file_path:
            self.resume_path_var.set(file_path)
            # Save the resume path to the current profile
            self.profile_manager.current_resume_path = file_path
            self.profile_manager.update_current_profile()
            self.save_status_label.config(
                text=f"Resume added to profile '{self.profile_manager.current_profile_name}'")
            self.app.root.after(
                2000, lambda: self.save_status_label.config(text=""))

            # Update the main tab
            self.app.update_tabs()

    def _remove_resume(self):
        """Remove resume from profile"""
        self.resume_path_var.set("")
        self.profile_manager.current_resume_path = None
        self.profile_manager.update_current_profile()
        self.save_status_label.config(
            text=f"Resume removed from profile '{self.profile_manager.current_profile_name}'")
        self.app.root.after(
            2000, lambda: self.save_status_label.config(text=""))

        # Update the main tab
        self.app.update_tabs()

    def _update_resume_path(self):
        """Update resume path field"""
        resume_path = self.profile_manager.current_resume_path
        if resume_path:
            self.resume_path_var.set(resume_path)
        else:
            self.resume_path_var.set("")

    def update(self):
        """Update the tab when profile changes"""
        self.personal_context_input.delete("1.0", tk.END)
        self.personal_context_input.insert(
            tk.END, self.profile_manager.current_personal_context)
        self._update_resume_path()


class SystemInstructionTab(TabBase):
    """Tab for managing system instruction templates"""

    def __init__(self, parent, app):
        """Initialize the system instruction tab"""
        super().__init__(parent)
        self.app = app
        self.profile_manager = ProfileManager()
        self.gemini_client = GeminiClient()

        tk.Label(self.frame, text="System Instruction Template:", font=(
            "Arial", 12, "bold")).pack(anchor="w", padx=10, pady=(10, 5))
        tk.Label(self.frame, text="Customize how the AI generates cover letters. DO NOT CHANGE UNLESS ABSOLUTELY NECESSARY.",
                 font=("Arial", 10, "italic")).pack(anchor="w", padx=10, pady=(0, 5))

        self.system_instruction_input = scrolledtext.ScrolledText(
            self.frame, height=15, width=80, wrap=tk.WORD, font=("Arial", 10))
        self.system_instruction_input.pack(
            fill=tk.BOTH, expand=True, padx=10, pady=5)
        self.system_instruction_input.insert(
            tk.END, self.profile_manager.current_system_template)
        self._add_context_menu(self.system_instruction_input)

        # Buttons frame for system template
        system_buttons_frame = tk.Frame(self.frame, padx=10)
        system_buttons_frame.pack(fill=tk.X, pady=5)

        save_system_button = tk.Button(system_buttons_frame, text="Apply Changes",
                                       command=self._save_system_instruction, bg="#4CAF50", fg="white", font=("Arial", 11))
        save_system_button.pack(side=tk.LEFT, padx=5)

        reset_system_button = tk.Button(system_buttons_frame, text="Reset to Default",
                                        command=self._reset_system_instruction, bg="#f44336", fg="white", font=("Arial", 11))
        reset_system_button.pack(side=tk.LEFT, padx=5)

        # System Core Rules section (moved from separate tab)
        system_core_frame = tk.LabelFrame(
            self.frame, text="System Core Rules", padx=10, pady=10, font=("Arial", 11, "bold"))
        system_core_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        tk.Label(system_core_frame, text="Define rules that will be added to the system instructions. Keep this short as it is sent with each prompt.",
                 font=("Arial", 10, "italic")).pack(anchor="w", pady=(0, 5))

        self.system_core_rules_input = scrolledtext.ScrolledText(
            system_core_frame, height=10, width=80, wrap=tk.WORD, font=("Arial", 10))
        self.system_core_rules_input.pack(fill=tk.BOTH, expand=True, pady=5)
        self.system_core_rules_input.insert(
            tk.END, self.profile_manager.current_system_core_rules)
        self._add_context_menu(self.system_core_rules_input)

        # Buttons frame for core rules
        core_rules_buttons_frame = tk.Frame(system_core_frame)
        core_rules_buttons_frame.pack(fill=tk.X, pady=5)

        save_rules_button = tk.Button(core_rules_buttons_frame, text="Apply Changes",
                                      command=self._save_system_core_rules, bg="#4CAF50", fg="white", font=("Arial", 11))
        save_rules_button.pack(side=tk.LEFT, padx=5)

        reset_rules_button = tk.Button(core_rules_buttons_frame, text="Reset to Empty",
                                       command=self._reset_system_core_rules, bg="#f44336", fg="white", font=("Arial", 11))
        reset_rules_button.pack(side=tk.LEFT, padx=5)

        # Cache management section
        cache_frame = tk.LabelFrame(
            self.frame, text="Cache Management", padx=10, pady=10, font=("Arial", 11, "bold"))
        cache_frame.pack(fill=tk.X, padx=10, pady=10)

        tk.Label(cache_frame, text="Cache stores your personal profile and system instructions to improve response time").pack(
            anchor="w")

        # Cache action buttons
        cache_buttons_frame = tk.Frame(cache_frame)
        cache_buttons_frame.pack(fill=tk.X, pady=5)

        clear_cache_button = tk.Button(cache_buttons_frame, text="Clear All Caches",
                                       command=self._clear_caches, bg="#f44336", fg="white", font=("Arial", 10))
        clear_cache_button.pack(side=tk.LEFT, padx=5)

        view_cache_button = tk.Button(cache_buttons_frame, text="View Cache Status", command=self._view_cache_status,
                                      bg="#2196F3", fg="white", font=("Arial", 10))
        view_cache_button.pack(side=tk.LEFT, padx=5)

        # Cache status label
        self.cache_status_label = tk.Label(
            cache_frame, text="", font=("Arial", 10, "italic"))
        self.cache_status_label.pack(pady=5)

        # Status label for the entire advanced settings tab
        self.status_label = tk.Label(self.frame, text="", font=(
            "Arial", 10, "italic"), fg="#4CAF50")
        self.status_label.pack(pady=5)

    def _save_system_instruction(self):
        """Save changes to system instruction template"""
        self.profile_manager.current_system_template = self.system_instruction_input.get(
            "1.0", tk.END)
        self.profile_manager.update_current_profile()

        self.status_label.config(
            text=f"System template saved successfully! Changes applied to '{self.profile_manager.current_profile_name}' profile.")
        self.app.root.after(2000, lambda: self.status_label.config(text=""))

    def _reset_system_instruction(self):
        """Reset system instruction template to default"""
        from config import DEFAULT_SYSTEM_INSTRUCTION_TEMPLATE
        self.system_instruction_input.delete("1.0", tk.END)
        self.system_instruction_input.insert(
            tk.END, DEFAULT_SYSTEM_INSTRUCTION_TEMPLATE)
        self.status_label.config(text="System template reset to default")
        self.app.root.after(2000, lambda: self.status_label.config(text=""))

    def _save_system_core_rules(self):
        """Save changes to system core rules"""
        self.profile_manager.current_system_core_rules = self.system_core_rules_input.get(
            "1.0", tk.END)
        self.profile_manager.update_current_profile()

        self.status_label.config(
            text=f"System core rules saved successfully! Changes applied to '{self.profile_manager.current_profile_name}' profile.")
        self.app.root.after(2000, lambda: self.status_label.config(text=""))

    def _reset_system_core_rules(self):
        """Reset system core rules to empty"""
        self.system_core_rules_input.delete("1.0", tk.END)
        self.status_label.config(text="System core rules reset to empty")
        self.app.root.after(2000, lambda: self.status_label.config(text=""))

    def _clear_caches(self):
        """Clear all cached content"""
        try:
            success = self.gemini_client.clear_caches()
            if success:
                self.cache_status_label.config(
                    text="All caches cleared successfully", fg="#4CAF50")
            else:
                self.cache_status_label.config(
                    text="Error clearing caches", fg="#f44336")
            self.app.root.after(
                3000, lambda: self.cache_status_label.config(text=""))
        except Exception as e:
            self.cache_status_label.config(
                text=f"Error: {str(e)}", fg="#f44336")
            self.app.root.after(
                3000, lambda: self.cache_status_label.config(text=""))

    def _view_cache_status(self):
        """View information about active caches"""
        try:
            active_caches = self.gemini_client.cache_manager.get_active_caches_info()

            # Create a popup window to display cache info
            cache_window = tk.Toplevel(self.app.root)
            cache_window.title("Cache Status")
            cache_window.geometry("500x300")

            tk.Label(cache_window, text="Active Cache Information",
                     font=("Arial", 12, "bold")).pack(pady=(10, 5))

            if active_caches:
                # Create a frame for the cache list
                list_frame = tk.Frame(cache_window)
                list_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

                # Headers
                tk.Label(list_frame, text="Cache Name", font=("Arial", 10, "bold"), width=30).grid(
                    row=0, column=0, sticky="w", padx=5, pady=2)
                tk.Label(list_frame, text="Minutes Remaining", font=(
                    "Arial", 10, "bold"), width=15).grid(row=0, column=1, sticky="w", padx=5, pady=2)

                # Add a separator
                separator = ttk.Separator(list_frame, orient='horizontal')
                separator.grid(row=1, column=0, columnspan=2,
                               sticky="ew", pady=5)

                # List each cache
                for i, cache in enumerate(active_caches):
                    tk.Label(list_frame, text=cache["name"], width=30).grid(
                        row=i+2, column=0, sticky="w", padx=5, pady=2)
                    tk.Label(list_frame, text=str(cache["minutes_remaining"]), width=15).grid(
                        row=i+2, column=1, sticky="w", padx=5, pady=2)

                # Info about cache usage
                tk.Label(cache_window, text="These caches store your profile and system instruction to speed up responses.", font=(
                    "Arial", 10, "italic")).pack(pady=5)
            else:
                tk.Label(cache_window, text="No active caches found",
                         font=("Arial", 11)).pack(pady=20)
                tk.Label(cache_window, text="Caches are created when generating cover letters\nand automatically expire after 30 minutes.", font=(
                    "Arial", 10, "italic")).pack(pady=5)

            # Close button
            close_button = tk.Button(
                cache_window, text="Close", command=cache_window.destroy, bg="#2196F3", fg="white", font=("Arial", 10))
            close_button.pack(pady=10)
        except Exception as e:
            self.cache_status_label.config(
                text=f"Error retrieving cache info: {str(e)}", fg="#f44336")
            self.app.root.after(
                3000, lambda: self.cache_status_label.config(text=""))

    def update(self):
        """Update the tab when profile changes"""
        self.system_instruction_input.delete("1.0", tk.END)
        self.system_instruction_input.insert(
            tk.END, self.profile_manager.current_system_template)
        self.system_core_rules_input.delete("1.0", tk.END)
        self.system_core_rules_input.insert(
            tk.END, self.profile_manager.current_system_core_rules)


class ProfileManagementTab(TabBase):
    """Tab for managing multiple profiles"""

    def __init__(self, parent, app):
        """Initialize the profile management tab"""
        super().__init__(parent)
        self.app = app
        self.profile_manager = ProfileManager()

        tk.Label(self.frame, text="Profile Management", font=(
            "Arial", 14, "bold")).pack(anchor="w", padx=10, pady=10)
        tk.Label(self.frame, text="Save and switch between different profiles for various job types",
                 font=("Arial", 10, "italic")).pack(anchor="w", padx=10, pady=(0, 10))

        # Profile selection frame
        profile_selection_frame = tk.Frame(self.frame, padx=10, pady=10)
        profile_selection_frame.pack(fill=tk.X)

        tk.Label(profile_selection_frame, text="Current Profile:",
                 font=("Arial", 11)).pack(side=tk.LEFT, padx=5)

        # Profile dropdown
        self.profile_var = tk.StringVar(
            value=self.profile_manager.current_profile_name)
        self.profile_dropdown = ttk.Combobox(
            profile_selection_frame, textvariable=self.profile_var, state="readonly", width=30)
        self.profile_dropdown.pack(side=tk.LEFT, padx=5)

        # Initial population of the dropdown
        self._update_profile_dropdown()

        # Profile action buttons frame
        profile_actions_frame = tk.Frame(self.frame, padx=10, pady=10)
        profile_actions_frame.pack(fill=tk.X)

        # Profile action buttons
        load_button = tk.Button(profile_actions_frame, text="Load Selected Profile",
                                command=self._load_selected_profile, bg="#2196F3", fg="white", font=("Arial", 11))
        load_button.pack(side=tk.LEFT, padx=5)

        save_button = tk.Button(profile_actions_frame, text="Save Current Profile",
                                command=self._save_current_profile, bg="#4CAF50", fg="white", font=("Arial", 11))
        save_button.pack(side=tk.LEFT, padx=5)

        new_button = tk.Button(profile_actions_frame, text="Create New Profile",
                               command=self._create_new_profile, bg="#FF9800", fg="white", font=("Arial", 11))
        new_button.pack(side=tk.LEFT, padx=5)

        delete_button = tk.Button(profile_actions_frame, text="Delete Profile",
                                  command=self._delete_selected_profile, bg="#f44336", fg="white", font=("Arial", 11))
        delete_button.pack(side=tk.LEFT, padx=5)

        resume_button = tk.Button(profile_actions_frame, text="Add Resume PDF",
                                  command=self._add_resume_to_profile, bg="#9C27B0", fg="white", font=("Arial", 11))
        resume_button.pack(side=tk.LEFT, padx=5)

        # Profile status label
        self.profile_status_label = tk.Label(
            self.frame, text="", font=("Arial", 10, "italic"), fg="#4CAF50")
        self.profile_status_label.pack(pady=10)

        # Profile descriptions
        profile_desc_frame = tk.Frame(self.frame, padx=10, pady=5)
        profile_desc_frame.pack(fill=tk.BOTH, expand=True)

        tk.Label(profile_desc_frame, text="Profile Templates", font=(
            "Arial", 12, "bold")).pack(anchor="w", pady=(10, 5))

        # Example profiles suggestions
        examples_frame = tk.Frame(profile_desc_frame)
        examples_frame.pack(fill=tk.BOTH, expand=True)

        profile_examples = [
            {
                "name": "Software Developer",
                "desc": "For applying to programming and software engineering positions"
            },
            {
                "name": "Data Scientist",
                "desc": "For applying to data analysis and machine learning positions"
            },
            {
                "name": "Mechanical Engineer",
                "desc": "For applying to mechanical engineering and manufacturing roles"
            },
            {
                "name": "Project Manager",
                "desc": "For applying to project management and leadership positions"
            },
            {
                "name": "Construction Manager",
                "desc": "For applying to construction and site management roles"
            }
        ]

        for i, example in enumerate(profile_examples):
            frame = tk.Frame(examples_frame, relief=tk.RIDGE, bd=2)
            frame.grid(row=i//2, column=i % 2, padx=10, pady=5, sticky="nsew")

            tk.Label(frame, text=example["name"], font=(
                "Arial", 11, "bold")).pack(anchor="w", padx=5, pady=5)
            tk.Label(frame, text=example["desc"], wraplength=200).pack(
                anchor="w", padx=5, pady=5)

        # Configure the grid layout
        examples_frame.columnconfigure(0, weight=1)
        examples_frame.columnconfigure(1, weight=1)

    def _update_profile_dropdown(self):
        """Update the profile dropdown with available profiles"""
        profiles = self.profile_manager.list_profiles()
        if not profiles:
            profiles = ["Default"]
            # Save the default profile if it doesn't exist
            self.profile_manager.save_profile(
                "Default", self.profile_manager.current_personal_context, self.profile_manager.current_system_template)
        self.profile_dropdown['values'] = profiles
        return profiles

    def _load_selected_profile(self):
        """Load the selected profile"""
        selected = self.profile_var.get()
        if selected:
            if self.profile_manager.set_current_profile(selected):
                # Update all tabs
                self.app.update_tabs()

                self.profile_status_label.config(
                    text=f"Loaded profile: {selected}")
                self.app.root.after(
                    2000, lambda: self.profile_status_label.config(text=""))

    def _save_current_profile(self):
        """Save current settings to a profile"""
        name = simpledialog.askstring(
            "Save Profile", "Enter profile name:", initialvalue=self.profile_manager.current_profile_name)
        if name:
            # Current settings are already in the profile manager
            self.profile_manager.current_profile_name = name
            self.profile_manager.update_current_profile()

            self.profile_status_label.config(text=f"Saved profile: {name}")
            self.app.root.after(
                2000, lambda: self.profile_status_label.config(text=""))

            # Update the dropdown with the new profile
            profiles = self._update_profile_dropdown()
            self.profile_var.set(name)

            # Update all tabs
            self.app.update_tabs()

    def _delete_selected_profile(self):
        """Delete the selected profile"""
        selected = self.profile_var.get()
        if selected and selected != "Default":
            confirm = messagebox.askyesno(
                "Confirm Delete", f"Are you sure you want to delete the profile '{selected}'?")
            if confirm:
                if self.profile_manager.delete_profile(selected):
                    self.profile_status_label.config(
                        text=f"Deleted profile: {selected}")
                    profiles = self._update_profile_dropdown()
                    self.profile_var.set(profiles[0])

                    # Load the first profile after deletion
                    self._load_selected_profile()
                else:
                    self.profile_status_label.config(
                        text=f"Error deleting profile")
                self.app.root.after(
                    2000, lambda: self.profile_status_label.config(text=""))
        elif selected == "Default":
            messagebox.showinfo(
                "Cannot Delete", "The Default profile cannot be deleted.")

    def _create_new_profile(self):
        """Create a new profile from scratch"""
        name = simpledialog.askstring("New Profile", "Enter new profile name:")
        if name:
            confirm = messagebox.askyesno(
                "Confirm", "Start with blank profile? Select 'No' to use current settings.")

            from config import DEFAULT_SYSTEM_INSTRUCTION_TEMPLATE
            if confirm:
                # Start with a blank personal context
                self.profile_manager.save_profile(
                    name, "", DEFAULT_SYSTEM_INSTRUCTION_TEMPLATE)
            else:
                # Use current settings
                self.profile_manager.save_profile(
                    name,
                    self.profile_manager.current_personal_context,
                    self.profile_manager.current_system_template,
                    self.profile_manager.current_resume_path
                )

            # Update dropdown and select the new profile
            profiles = self._update_profile_dropdown()
            self.profile_var.set(name)

            # Load the new profile
            self._load_selected_profile()

    def _add_resume_to_profile(self):
        """Add a resume to the selected profile"""
        selected = self.profile_var.get()
        if selected:
            file_path = filedialog.askopenfilename(
                title=f"Select Resume PDF for {selected} profile",
                filetypes=[("PDF Files", "*.pdf"), ("All Files", "*.*")]
            )
            if file_path:
                profile_data = self.profile_manager.load_profile(selected)
                if profile_data:
                    personal_context = profile_data.get("personal_context", "")
                    system_template = profile_data.get("system_template", "")
                    self.profile_manager.save_profile(
                        selected, personal_context, system_template, file_path)

                    # If this is the current profile, update it
                    if selected == self.profile_manager.current_profile_name:
                        self.profile_manager.current_resume_path = file_path
                        self.app.update_tabs()

                    self.profile_status_label.config(
                        text=f"Resume added to profile: {selected}")
                    self.app.root.after(
                        2000, lambda: self.profile_status_label.config(text=""))

    def update(self):
        """Update the tab when profile changes"""
        self.profile_var.set(self.profile_manager.current_profile_name)


class SettingsTab(TabBase):
    """Tab for application settings including API key and model management"""

    def __init__(self, parent, app):
        """Initialize the settings tab"""
        super().__init__(parent)
        self.app = app
        self.profile_manager = ProfileManager()
        self.gemini_client = GeminiClient()

        # Create frames
        self.settings_frame = tk.Frame(self.frame, padx=10, pady=10)
        self.settings_frame.pack(
            fill=tk.BOTH, expand=True)        # API Key Section
        self.api_key_frame = tk.LabelFrame(self.settings_frame, text="API Key Configuration", font=(
            "Arial", 12, "bold"), padx=10, pady=10)
        self.api_key_frame.pack(fill=tk.X, pady=10)

        # API Key warning frame (container for warning label and copy button)
        self.api_key_warning_frame = tk.Frame(self.api_key_frame)

        # API key warning label (initially hidden)
        self.api_key_warning = tk.Label(
            self.api_key_warning_frame,
            text="Please enter your Google Gemini API key. You can get a free API key from https://aistudio.google.com/app/apikey",
            fg="#f44336", font=("Arial", 10, "italic"), wraplength=500)
        self.api_key_warning.pack(side=tk.LEFT)

        # Copy link button
        self.copy_link_button = tk.Button(self.api_key_warning_frame, text="Copy Link",
                                          command=self._copy_api_key_link, bg="#2196F3", fg="white", font=("Arial", 10))
        self.copy_link_button.pack(side=tk.LEFT, padx=5)

        # API Key input
        self.api_key_var = tk.StringVar(value=GEMINI_API_KEY)
        self.api_key_entry = tk.Entry(
            self.api_key_frame, textvariable=self.api_key_var, width=60, show="*")
        self.api_key_entry.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        self._add_context_menu(self.api_key_entry)

        # Toggle visibility
        self.show_key_var = tk.BooleanVar(value=False)
        self.show_key_check = tk.Checkbutton(
            self.api_key_frame, text="Show Key", variable=self.show_key_var, command=self._toggle_key_visibility)
        self.show_key_check.pack(side=tk.LEFT, padx=5)

        # API Key buttons
        self.api_key_buttons_frame = tk.Frame(self.api_key_frame)
        self.api_key_buttons_frame.pack(fill=tk.X, pady=5)

        self.save_key_button = tk.Button(self.api_key_buttons_frame, text="Save API Key",
                                         command=self._save_api_key, bg="#4CAF50", fg="white")
        self.save_key_button.pack(side=tk.LEFT, padx=5)

        self.clear_key_button = tk.Button(
            self.api_key_buttons_frame, text="Clear API Key", command=self._clear_api_key, bg="#f44336", fg="white")
        self.clear_key_button.pack(side=tk.LEFT, padx=5)

        # File Saving Options Section
        self.file_saving_frame = tk.LabelFrame(
            self.settings_frame, text="File Saving Options", font=("Arial", 12, "bold"), padx=10, pady=10)
        self.file_saving_frame.pack(fill=tk.X, pady=10)

        # Get current save preferences
        save_prefs = self.profile_manager.get_save_preferences()

        # Default folder selection
        self.default_folder_frame = tk.Frame(self.file_saving_frame)
        self.default_folder_frame.pack(fill=tk.X, pady=5)

        # Remember default folder checkbox
        self.remember_folder_var = tk.BooleanVar(
            value=save_prefs.get("always_use_default_folder", False))
        self.remember_folder_check = tk.Checkbutton(
            self.default_folder_frame, text="Always use this folder for saving (don't ask every time)", variable=self.remember_folder_var, command=self._toggle_folder_entry)
        self.remember_folder_check.pack(anchor="w", pady=5)

        # Default folder path
        self.folder_frame = tk.Frame(self.file_saving_frame)
        self.folder_frame.pack(fill=tk.X, pady=5)

        tk.Label(self.folder_frame, text="Default save folder:").pack(
            side=tk.LEFT, padx=5)

        self.default_folder_var = tk.StringVar(
            value=save_prefs.get("save_folder", ""))
        self.default_folder_entry = tk.Entry(
            self.folder_frame, textvariable=self.default_folder_var, width=50)
        self.default_folder_entry.pack(
            side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        self._add_context_menu(self.default_folder_entry)

        self.browse_folder_button = tk.Button(
            self.folder_frame, text="Browse...", command=self._browse_default_folder, bg="#2196F3", fg="white")
        self.browse_folder_button.pack(side=tk.LEFT, padx=5)

        # Initially disable the folder path controls if checkbox is unchecked
        if not self.remember_folder_var.get():
            self.default_folder_entry.config(state=tk.DISABLED)
            self.browse_folder_button.config(state=tk.DISABLED)

        # Auto-save option
        self.auto_save_var = tk.BooleanVar(
            value=save_prefs.get("auto_save_as_word", False))
        self.auto_save_check = tk.Checkbutton(self.file_saving_frame,
                                              text="Automatically save as Word file after generation is complete",
                                              variable=self.auto_save_var)
        self.auto_save_check.pack(anchor="w", pady=5)

        # File conflict handling
        self.file_conflict_frame = tk.LabelFrame(
            self.file_saving_frame, text="When a file with the same name already exists:", padx=10, pady=5)
        self.file_conflict_frame.pack(fill=tk.X, pady=5)

        self.conflict_handling_var = tk.BooleanVar(
            value=save_prefs.get("overwrite_existing_files", False))

        self.overwrite_radio = tk.Radiobutton(
            self.file_conflict_frame, text="Overwrite existing file", variable=self.conflict_handling_var, value=True)
        self.overwrite_radio.pack(anchor="w", pady=2)

        self.add_number_radio = tk.Radiobutton(
            self.file_conflict_frame, text="Add a number to the filename (e.g. CoverLetter_1.docx)", variable=self.conflict_handling_var, value=False)
        self.add_number_radio.pack(anchor="w", pady=2)

        # Save preferences button
        self.save_prefs_button = tk.Button(
            self.file_saving_frame, text="Save File Preferences", command=self._save_file_preferences, bg="#4CAF50", fg="white")
        self.save_prefs_button.pack(anchor="w", pady=10)

        # Model Selection Section
        self.model_frame = tk.LabelFrame(self.settings_frame, text="Model Configuration", font=(
            "Arial", 12, "bold"), padx=10, pady=10)
        self.model_frame.pack(fill=tk.X, pady=10)

        # Profile-specific model selection
        tk.Label(self.model_frame, text=f"Current Profile: {self.profile_manager.current_profile_name}", font=(
            "Arial", 10, "bold")).pack(anchor="w", pady=5)

        # Model dropdown
        self.model_selection_frame = tk.Frame(self.model_frame)
        self.model_selection_frame.pack(fill=tk.X, pady=5)

        tk.Label(self.model_selection_frame, text="Select Model:").pack(
            side=tk.LEFT, padx=5)

        self.model_var = tk.StringVar(value=self.profile_manager.current_model)
        self.model_dropdown = ttk.Combobox(
            self.model_selection_frame, textvariable=self.model_var, width=40, state="readonly")
        self.update_model_dropdown()
        self.model_dropdown.pack(side=tk.LEFT, padx=5)

        self.save_model_button = tk.Button(
            self.model_selection_frame, text="Save Model Selection", command=self._save_model_selection, bg="#4CAF50", fg="white")
        self.save_model_button.pack(side=tk.LEFT, padx=5)

        # Custom model management
        self.custom_model_frame = tk.LabelFrame(
            self.model_frame, text="Custom Models", padx=10, pady=10)
        self.custom_model_frame.pack(fill=tk.X, pady=10)

        # Add custom model
        self.add_model_frame = tk.Frame(self.custom_model_frame)
        self.add_model_frame.pack(fill=tk.X, pady=5)

        self.custom_model_var = tk.StringVar()
        tk.Label(self.add_model_frame, text="Model Name:").pack(
            side=tk.LEFT, padx=5)
        self.custom_model_entry = tk.Entry(
            self.add_model_frame, textvariable=self.custom_model_var, width=40)
        self.custom_model_entry.pack(side=tk.LEFT, padx=5)
        self._add_context_menu(self.custom_model_entry)

        self.add_model_button = tk.Button(
            self.add_model_frame, text="Add Model", command=self._add_custom_model, bg="#2196F3", fg="white")
        self.add_model_button.pack(side=tk.LEFT, padx=5)

        # List of custom models
        self.custom_models_list_frame = tk.Frame(self.custom_model_frame)
        self.custom_models_list_frame.pack(fill=tk.BOTH, expand=True, pady=5)

        tk.Label(self.custom_models_list_frame,
                 text="Custom Models:").pack(anchor="w")

        self.custom_models_listbox = tk.Listbox(
            self.custom_models_list_frame, height=5, width=50)
        self.custom_models_listbox.pack(
            side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5)
        self._add_listbox_context_menu(self.custom_models_listbox)

        # Scrollbar for custom models listbox
        self.custom_models_scrollbar = tk.Scrollbar(
            self.custom_models_list_frame, orient=tk.VERTICAL, command=self.custom_models_listbox.yview)
        self.custom_models_listbox.config(
            yscrollcommand=self.custom_models_scrollbar.set)
        self.custom_models_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Update the listbox
        self._update_custom_models_list()

        # Delete custom model button
        self.delete_model_button = tk.Button(self.custom_model_frame, text="Delete Selected Custom Model",
                                             command=self._delete_custom_model, bg="#f44336", fg="white")
        self.delete_model_button.pack(anchor="w", pady=5)

        # Status message
        self.status_label = tk.Label(
            self.settings_frame, text="", font=("Arial", 10, "italic"))
        self.status_label.pack(pady=10)

    def _toggle_key_visibility(self):
        """Toggle API key visibility"""
        if self.show_key_var.get():
            self.api_key_entry.config(show="")
        else:
            self.api_key_entry.config(show="*")

    def _save_api_key(self):
        """Save the API key to settings file"""
        new_key = self.api_key_var.get().strip()

        if not new_key:
            self.status_label.config(
                text="API key cannot be empty!", fg="#f44336")
            return

        # Update the settings file
        settings = load_settings()
        settings["api_key"] = new_key
        if save_settings(settings):            # Update the client
            if self.gemini_client.update_api_key(new_key):
                self.status_label.config(
                    text="API key saved successfully!", fg="#4CAF50")
                # Hide the API key warning frame if it's visible
                self.api_key_warning_frame.pack_forget()
            else:
                self.status_label.config(
                    text="Error updating API client with new key.", fg="#f44336")
        else:
            self.status_label.config(
                text="Error saving API key to settings file.", fg="#f44336")

    def _clear_api_key(self):
        """Clear the API key"""
        if messagebox.askyesno("Confirm", "Are you sure you want to clear the API key?"):
            self.api_key_var.set("")
            settings = load_settings()
            settings["api_key"] = ""
            if save_settings(settings):
                self.gemini_client.update_api_key("")
                self.status_label.config(text="API key cleared.", fg="#4CAF50")
            else:
                self.status_label.config(
                    text="Error clearing API key in settings file.", fg="#f44336")

    def _copy_api_key_link(self):
        """Copy the API key link to clipboard"""
        api_key_url = "https://aistudio.google.com/app/apikey"
        self.app.root.clipboard_clear()
        self.app.root.clipboard_append(api_key_url)

        # Create a temporary status label for feedback
        status_label = tk.Label(
            self.api_key_warning_frame, text="Link copied!", fg="#4CAF50", font=("Arial", 10, "italic"))
        status_label.pack(side=tk.LEFT, padx=10)

        # Remove the status label after 2 seconds
        self.app.root.after(2000, lambda: status_label.destroy())

    def update_model_dropdown(self):
        """Update the model dropdown with all available models"""
        settings = load_settings()
        models = settings.get("default_models", []) + \
            settings.get("custom_models", [])
        self.model_dropdown["values"] = models

        # Select current model
        if self.profile_manager.current_model in models:
            self.model_var.set(self.profile_manager.current_model)
        elif models:
            self.model_var.set(models[0])

    def _save_model_selection(self):
        """Save the selected model for the current profile"""
        selected_model = self.model_var.get()
        if not selected_model:
            self.status_label.config(
                text="Please select a model!", fg="#f44336")
            return

        # Update profile manager
        self.profile_manager.current_model = selected_model
        self.profile_manager.update_current_profile()

        # Update gemini client
        self.gemini_client.update_model(selected_model)

        self.status_label.config(
            text=f"Model {selected_model} saved for profile {self.profile_manager.current_profile_name}.", fg="#4CAF50")

    def _add_custom_model(self):
        """Add a custom model to the settings"""
        model_name = self.custom_model_var.get().strip()

        if not model_name:
            self.status_label.config(
                text="Model name cannot be empty!", fg="#f44336")
            return

        settings = load_settings()
        default_models = settings.get("default_models", [])
        custom_models = settings.get("custom_models", [])

        # Check if model already exists
        if model_name in default_models:
            self.status_label.config(
                text=f"Model {model_name} is already in the default models!", fg="#f44336")
            return

        if model_name in custom_models:
            self.status_label.config(
                text=f"Model {model_name} is already in custom models!", fg="#f44336")
            return

        # Add the model
        custom_models.append(model_name)
        settings["custom_models"] = custom_models

        if save_settings(settings):
            self._update_custom_models_list()
            self.update_model_dropdown()
            self.custom_model_var.set("")  # Clear the entry
            self.status_label.config(
                text=f"Model {model_name} added successfully!", fg="#4CAF50")
        else:
            self.status_label.config(
                text="Error saving custom model to settings file.", fg="#f44336")

    def _update_custom_models_list(self):
        """Update the listbox with custom models"""
        settings = load_settings()
        custom_models = settings.get("custom_models", [])

        self.custom_models_listbox.delete(0, tk.END)  # Clear existing items

        for model in custom_models:
            self.custom_models_listbox.insert(tk.END, model)

        self._add_listbox_context_menu(self.custom_models_listbox)

    def _delete_custom_model(self):
        """Delete the selected custom model"""
        selected_indices = self.custom_models_listbox.curselection()

        if not selected_indices:
            self.status_label.config(
                text="Please select a model to delete!", fg="#f44336")
            return

        selected_index = selected_indices[0]
        selected_model = self.custom_models_listbox.get(selected_index)

        if messagebox.askyesno("Confirm", f"Are you sure you want to delete the model '{selected_model}'?"):
            settings = load_settings()
            custom_models = settings.get("custom_models", [])

            if selected_model in custom_models:
                custom_models.remove(selected_model)
                settings["custom_models"] = custom_models

                if save_settings(settings):
                    self._update_custom_models_list()
                    self.update_model_dropdown()

                    # If current profile is using this model, switch to default
                    if self.profile_manager.current_model == selected_model:
                        self.profile_manager.current_model = DEFAULT_GEMINI_MODEL
                        self.profile_manager.update_current_profile()
                        self.gemini_client.update_model(DEFAULT_GEMINI_MODEL)
                        self.model_var.set(DEFAULT_GEMINI_MODEL)

                    self.status_label.config(
                        text=f"Model {selected_model} deleted successfully!", fg="#4CAF50")
                else:
                    self.status_label.config(
                        text="Error saving settings after deleting model.", fg="#f44336")

    def _toggle_folder_entry(self):
        """Enable or disable the folder entry based on checkbox state"""
        if self.remember_folder_var.get():
            self.default_folder_entry.config(state=tk.NORMAL)
            self.browse_folder_button.config(state=tk.NORMAL)
        else:
            self.default_folder_entry.config(state=tk.DISABLED)
            self.browse_folder_button.config(state=tk.DISABLED)

    def _browse_default_folder(self):
        """Browse for default save folder"""
        folder_path = filedialog.askdirectory(
            title="Select Default Save Folder")
        if folder_path:
            self.default_folder_var.set(folder_path)

    def _save_file_preferences(self):
        """Save file handling preferences"""
        always_use_default = self.remember_folder_var.get()
        auto_save = self.auto_save_var.get()
        overwrite_files = self.conflict_handling_var.get()

        # Only save folder path if "always use this folder" is checked
        save_folder = self.default_folder_var.get() if always_use_default else None

        # Update profile manager
        self.profile_manager.set_save_preferences(
            always_use_default=always_use_default,            auto_save=auto_save,
            overwrite_files=overwrite_files,
            save_folder=save_folder
        )
        self.status_label.config(
            text="File preferences saved successfully!", fg="#4CAF50")
        self.app.root.after(2000, lambda: self.status_label.config(text=""))

    def update(self):
        """Update the settings tab when profile changes"""
        # Update profile name label
        for widget in self.model_frame.winfo_children():
            if isinstance(widget, tk.Label) and widget.cget("text").startswith("Current Profile:"):
                widget.config(
                    text=f"Current Profile: {self.profile_manager.current_profile_name}")
                break

        # Update model selection
        self.model_var.set(self.profile_manager.current_model)

        # Update file saving preferences
        save_prefs = self.profile_manager.get_save_preferences()
        self.remember_folder_var.set(save_prefs.get(
            "always_use_default_folder", False))
        self.auto_save_var.set(save_prefs.get("auto_save_as_word", False))
        self.conflict_handling_var.set(
            save_prefs.get("overwrite_existing_files", False))
        self.default_folder_var.set(save_prefs.get("save_folder", ""))

        # Update folder entry state
        self._toggle_folder_entry()


class CoverLetterGeneratorApp:
    """Main application class"""

    def __init__(self):
        """Initialize the application"""
        self.root = tk.Tk()
        self.root.title("Cover Letter Generator")
        self.root.geometry("800x900")

        # Create notebook (tabbed interface)
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True)

        # Create tabs
        self.main_tab = MainTab(self.notebook, self)
        self.profile_tab = ProfileTab(self.notebook, self)
        self.system_tab = SystemInstructionTab(self.notebook, self)
        self.profiles_tab = ProfileManagementTab(self.notebook, self)
        self.settings_tab = SettingsTab(self.notebook, self)

        # Add tabs to notebook
        self.notebook.add(self.main_tab.get_frame(),
                          text="Generate Cover Letter")
        self.notebook.add(self.profile_tab.get_frame(),
                          text="Personal Profile")
        self.notebook.add(self.system_tab.get_frame(),
                          text="Advanced Settings")
        self.notebook.add(self.profiles_tab.get_frame(),
                          text="Profile Management")
        self.notebook.add(self.settings_tab.get_frame(), text="Settings")

        # Setup context menu for the entire application
        self._setup_global_context_menu()

    def _setup_global_context_menu(self):
        """Setup right-click context menu for any text labels and the application window"""
        # Create a global context menu
        global_menu = tk.Menu(self.root, tearoff=0)
        global_menu.add_command(label="Copy", command=self._copy_selected_text)

        # Add more options to make it behave like system default menu
        global_menu.add_separator()
        global_menu.add_command(label="Select All", command=self._select_all)

        # Bind the menu to right-click events on the root window
        self.root.bind(
            "<Button-3>", lambda event: self._show_global_context_menu(event, global_menu))

        # Make labels selectable
        self._make_labels_selectable(self.root)

    def _make_labels_selectable(self, parent):
        """Recursively make all labels in the application selectable"""
        for widget in parent.winfo_children():
            if isinstance(widget, tk.Label):
                # Enable selection for labels
                widget.bind(
                    "<Button-1>", lambda event: event.widget.focus_set())
                widget.bind(
                    "<Button-3>", lambda event: self._handle_label_right_click(event))

            # Recursively process child widgets
            if widget.winfo_children():
                self._make_labels_selectable(widget)

    def _handle_label_right_click(self, event):
        """Handle right-click on label widgets for copying text"""
        label = event.widget
        text = label.cget("text")

        # Create a temporary context menu just for this label
        temp_menu = tk.Menu(self.root, tearoff=0)
        temp_menu.add_command(
            label="Copy Text", command=lambda: self._copy_specific_text(text))

        # Show the menu
        try:
            temp_menu.tk_popup(event.x_root, event.y_root)
        finally:
            temp_menu.grab_release()

    def _copy_specific_text(self, text):
        """Copy specific text to clipboard"""
        self.root.clipboard_clear()
        self.root.clipboard_append(text)

    def _show_global_context_menu(self, event, menu):
        """Show the global context menu at mouse position"""
        try:
            menu.tk_popup(event.x_root, event.y_root)
        finally:
            menu.grab_release()

    def _copy_selected_text(self):
        """Copy any selected text to clipboard"""
        try:
            selected_text = self.root.selection_get()
            self.root.clipboard_clear()
            self.root.clipboard_append(selected_text)
        except:
            # No text selected or unable to get selection
            pass

    def _select_all(self):
        """Attempt to select all text in the current focused widget"""
        try:
            focused_widget = self.root.focus_get()
            if isinstance(focused_widget, (tk.Text, scrolledtext.ScrolledText)):
                focused_widget.tag_add(tk.SEL, "1.0", tk.END)
                focused_widget.mark_set(tk.INSERT, "1.0")
                focused_widget.see(tk.INSERT)
            elif isinstance(focused_widget, tk.Entry):
                focused_widget.select_range(0, tk.END)
                focused_widget.icursor(tk.END)
        except:
            # Unable to select all text
            pass

    def run(self):
        """Run the application"""
        # Check if API key is set
        api_key = GEMINI_API_KEY
        if not api_key:
            # Switch to settings tab and show a message
            # Index 4 corresponds to Settings tab            # Show the API key warning frame
            self.notebook.select(4)
            self.settings_tab.api_key_warning_frame.pack(
                pady=5, fill=tk.X, before=self.settings_tab.api_key_entry)

        self.root.mainloop()
