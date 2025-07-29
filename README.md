# Cover Letter Generator

A sophisticated AI-powered cover letter generator that creates personalized, professional cover letters using Google Gemini AI. The application features a modern desktop GUI, profile management, resume integration, and intelligent caching for optimal performance.

### 🚀 Quick Start

## Installation

- run `google ai coverletter/dist/CoverLetterGenerator.exe `

## 🌟 Features

### Core Functionality

- **AI-Powered Generation**: Leverages Google Gemini 2.0 Flash and other advanced models to create compelling cover letters
- **Smart Matching**: Intelligently matches your skills and experience with job requirements
- **Resume Integration**: Upload and integrate PDF resumes for enhanced context
- **Real-time Generation**: Watch your cover letter being generated in real-time with streaming responses

### Profile Management

- **Multiple Profiles**: Create and manage unlimited user profiles for different career paths
- **Personal Context**: Maintain detailed personal information, skills, and experiences per profile
- **Resume Attachment**: Associate specific resumes with each profile
- **Quick Switching**: Seamlessly switch between profiles for different job applications

### Intelligent Caching

- **Context Caching**: Automatically cache personal context to reduce API calls and improve response times
- **Session Management**: Maintain conversation context across multiple cover letter generations
- **TTL Management**: Configurable cache expiration (default: 59 minutes)
- **Cache Status**: Monitor active caches and their remaining time

### User Experience

- **Modern GUI**: Clean, intuitive Tkinter-based interface with tabbed navigation
- **Right-click Menus**: Context menus for copy/paste operations throughout the application
- **Export Options**: Save generated cover letters as Word documents (.docx)
- **Clipboard Integration**: One-click copying to clipboard
- **Error Handling**: Comprehensive error handling with user-friendly messages

### Customization

- **System Templates**: Customize AI instructions and core rules
- **Model Selection**: Choose from multiple Gemini models or add custom models
- **File Management**: Configure default save locations and file handling preferences
- **API Management**: Secure API key storage and management

## 🎯 Usage Tips

### Writing Effective Personal Context

- Include detailed information about your background and experiences
- Mention specific projects, technologies, and achievements
- Describe your passion and motivations in your field
- The more detailed your context, the better the AI can tailor cover letters

### Job Description Input

- Paste the complete job description for best results
- Include both required and preferred qualifications
- The AI will automatically match your skills with job requirements

### Profile Management

- Create separate profiles for different career paths
- Use descriptive names for easy identification
- Regularly update your personal context as you gain experience

### Optimizing AI Output

- Adjust system instructions to match your writing style
- Modify core rules to emphasize specific aspects
- Experiment with different Gemini models for varied outputs

## 🔧 Advanced Features

### System Instructions Customization

The application allows full customization of AI behavior through:

- **System Template**: High-level instructions for the AI
- **Core Rules**: Specific guidelines for cover letter generation
- **Model-Specific Settings**: Different instructions for different AI models

### Cache Management

- **Automatic Caching**: Personal context automatically cached for faster generation
- **Session Persistence**: Chat sessions saved and restored across app restarts
- **Smart Invalidation**: Caches automatically expire to ensure fresh content

### Resume Integration

- **PDF Support**: Upload PDF resumes for additional context
- **Profile Association**: Link specific resumes to different profiles
- **Intelligent Parsing**: AI extracts relevant information from resume content

### First-Time Setup

1. **Configure Your Profile**

   - Navigate to the "Profile" tab
   - Enter your personal information, skills, and experiences
   - Optionally upload a PDF resume
   - Save your profile

2. **Customize Instructions (Optional)**

   - Go to "System Instructions" tab
   - Modify the AI instructions to match your preferences
   - Adjust core rules for cover letter generation

3. **Generate Your First Cover Letter**
   - Switch to the "Main" tab
   - Paste a job description
   - Click "Generate Cover Letter"
   - Copy or save the result

## 🐛 Troubleshooting

### Common Issues

**API Key Problems**

- Ensure your API key is valid and has sufficient quota
- Check that the API key has access to Gemini models
- Verify network connectivity for API calls

**File Access Issues**

- Ensure the application has write permissions in its directory
- Check that PDF files are not corrupted or password-protected
- Verify sufficient disk space for cache and profile storage

**Generation Issues**

- Try clearing caches if output seems stale
- Ensure job description is detailed enough for matching
- Check that personal context contains relevant information

### Error Messages

- **"Invalid API Key"**: Verify your Google Gemini API key
- **"Model Not Available"**: Selected model may not be accessible with your API key
- **"File Not Found"**: Check file paths and permissions
- **"Cache Error"**: Try clearing all caches and restarting

## 🔄 Updates and Maintenance

### Keeping the Application Updated

- Regularly update the `google-genai` package for latest features
- Monitor Google AI Studio for new model releases
- Update system instructions based on changing job market trends

### Data Backup

- Regularly backup your `profiles/` directory
- Export important personal context files
- Save generated cover letters to prevent loss

## For developers

### Prerequisites

- Python 3.8 or higher
- Google Gemini API key ([Get one here](https://aistudio.google.com/app/apikey))
- Required Python packages (see Installation)

### Installation

1. **Clone or download the project**

   ```bash
   git clone <repository-url>
   cd google-ai-coverletter
   ```

2. **Install dependencies**

   ```bash
   pip install google-genai python-docx
   ```

3. **Run the application**

   ```bash
   python main.py
   ```

4. **Configure API Key**
   - Go to the Settings tab
   - Enter your Google Gemini API key
   - Select your preferred AI model
   - Save settings

## 📁 Project Structure

```
google-ai-coverletter/
├── main.py                 # Application entry point
├── gui.py                  # Main GUI implementation
├── gemini_client.py        # Google Gemini API client
├── profile_manager.py      # Profile management system
├── cache_manager.py        # Intelligent caching system
├── local_storage_manager.py # Local file storage management
├── config.py              # Configuration and settings
├── settings.json          # Application settings
├── build_exe.py           # Windows executable builder
├── build_mac.py           # macOS app bundle builder
├── sign_mac_app.py        # macOS app signing
├── create_icon.py         # Icon generation utility
├── profiles/              # User profiles storage
│   └── Default.json       # Default profile
├── personal_context/      # Personal context files
│   └── Default.txt        # Default personal context
├── chat_states/           # Cached chat sessions
├── cache/                 # API cache storage
└── files/                 # File storage
    └── storage/           # Uploaded files
        ├── icon.ico       # Application icon
        └── icon.png       # Icon source
```

## 🔧 Configuration

### API Settings

- **API Key**: Your Google Gemini API key
- **Model Selection**: Choose from available Gemini models
- **Custom Models**: Add and manage custom model endpoints

### Profile Settings

- **Personal Context**: Your background, skills, and experiences
- **Resume**: Upload PDF resumes for enhanced context
- **System Instructions**: Customize AI behavior and rules

### File Management

- **Default Save Location**: Set where cover letters are saved
- **Auto-save**: Automatically save generated cover letters
- **File Overwrite**: Configure file overwrite behavior

### Cache Management

- **TTL (Time To Live)**: Set cache expiration time (default: 59 minutes)
- **Cache Clearing**: Clear all cached contexts when needed
- **Cache Status**: Monitor active caches and their status

## 🏗️ Building Executables

### Windows Executable

```bash
python build_exe.py
```

Creates a standalone `.exe` file in the `dist/` directory.

### macOS App Bundle

```bash
python build_mac.py
```

Creates a `.app` bundle for macOS with universal2 architecture support.

### Build Features

- **Single File Distribution**: All dependencies bundled
- **Data Inclusion**: Profiles, cache, and settings included
- **Icon Support**: Custom application icon
- **Platform Optimization**: Optimized for target platforms

## 🔒 Security & Privacy

- **Local Storage**: All data stored locally, no cloud dependencies
- **API Key Security**: Encrypted storage of API credentials
- **No Data Collection**: No telemetry or usage data collection
- **Offline Profiles**: Profile data works offline (except AI generation)

## 📄 License

This project is provided as-is for educational and personal use. Please ensure compliance with Google's Gemini API terms of service.

## 🤝 Contributing

While this is a personal project, suggestions and improvements are welcome. Please ensure any modifications maintain the security and privacy standards of the application.

## 📞 Support

For issues related to:

- **Google Gemini API**: Consult [Google AI Studio documentation](https://aistudio.google.com/app/apikey)
- **Application Bugs**: Check the troubleshooting section above
- **Feature Requests**: Consider customizing system instructions or profiles

---

**Made with ❤️ for job seekers everywhere. Good luck with your applications!**
