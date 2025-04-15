# Alumni Association Platform

A modern web application for alumni to connect, share ideas, and give back to their alma mater.

[Alumni Association]

## Features

- **User Authentication**: Secure login and registration system
- **Dashboard**: Personalized dashboard for alumni to interact with the community
- **Networking**: Connect with fellow alumni and build professional relationships
- **Q&A Platform**: Ask questions and get answers from the alumni community
- **Sharing**: Share ideas, projects, and success stories
- **Events**: Stay updated with upcoming alumni events
- **Donations**: Support your alma mater through secure donations
- **Profile Management**: Maintain and update your alumni profile

## Technology Stack

- **Frontend**: HTML, CSS, JavaScript, Bootstrap 5
- **Backend**: Python, Flask
- **Database**: MongoDB
- **Authentication**: Flask-Login
- **Styling**: Custom CSS with modern design elements

## Installation

1. Clone the repository:
   ```
   git clone https://github.com/yourusername/alumni-association.git
   cd alumni-association
   ```

2. Create a virtual environment and activate it:
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

4. Set up MongoDB:
   - Make sure MongoDB is installed and running on your system
   - The application will connect to `mongodb://localhost:27017/` by default

5. Run the application:
   ```
   python app.py
   ```

6. Access the application at `http://localhost:5000`

## Project Structure

```
alumni-association/
├── app.py                  # Main application file
├── requirements.txt        # Python dependencies
├── templates/              # HTML templates
│   ├── base.html           # Base template with common elements
│   ├── home.html           # Home page
│   ├── login.html          # Login page
│   ├── signup.html         # Registration page
│   ├── dashboard.html      # User dashboard
│   ├── profile.html        # User profile
│   └── donate.html         # Donation page
└── static/                 # Static files (CSS, JS, images)
```

## Usage

1. **Registration**: New users can sign up with their name, email, and password
2. **Login**: Registered users can log in to access their dashboard
3. **Dashboard**: View and interact with questions, posts, and events
4. **Profile**: Update personal information and view contributions
5. **Donations**: Make contributions to support the institution

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- Font Awesome for icons
- Google Fonts for typography
- Bootstrap for responsive design components

---

**Note**: This is a demo application for educational purposes. For production use, additional security measures and features should be implemented. 
