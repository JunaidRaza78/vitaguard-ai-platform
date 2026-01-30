# Professional Auth and Email Services

This directory contains production-ready, standalone modules for Google Authentication and Email Services.

## Features

-   **Standard Config**: Uses a standard `.env` file for configuration logic.
-   **Type Safety**: Fully type-hinted methods.
-   **Logging**: Integrated logging for debugging.
-   **Error Handling**: Robust exception management.

## Setup

1.  **Keys**:
    *   Navigate to the `keys/` directory.
    *   **Security Note**: Ensure `keys/.env` is added to your `.gitignore`.

2.  **Dependencies**:
    *   Install via pip: `pip install authlib starlette requests python-dotenv`

## Usage

### Google Auth
```python
import logging
from auth_export.google_auth import GoogleAuth

# (Optional) specific logging config
logging.basicConfig(level=logging.INFO)

# Initialize
google_auth = GoogleAuth()
oauth = google_auth.get_oauth()
```

### Email Service
```python
from auth_export.email_service import EmailService

# Initialize
emailer = EmailService()

# Send
success = emailer.send_email("recipient@example.com", "Subject", "<h1>Hello</h1>")
```
