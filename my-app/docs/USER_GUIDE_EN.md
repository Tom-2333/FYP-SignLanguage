# Sign Language Learning Platform User Guide (English)

## 1. Purpose
This guide explains how to use the main features of the platform:
- Register and log in
- Practice vocabulary with gesture recognition
- Generate sign-language style sentences and manage chat history
- Browse support resources
- Configure language, theme, font size, and accessibility settings

This document is based on the current frontend pages and the provided screenshots.

## 2. Requirements and Preparation
### 2.1 Basic Requirements
- A modern browser (Chrome recommended)
- Camera permission enabled (for gesture practice)
- Reachable database API and gesture recognition service

### 2.2 Gesture Service Startup
If the vocabulary page shows connecting or offline status, start the gesture backend service:
1. Open a terminal and move to the cv_hands folder.
2. Run with Python 3.10:

```bash
py -3.10 app_simple.py
```

3. Default endpoints:
- Health: http://127.0.0.1:5001/api/v1/health
- WebSocket: ws://127.0.0.1:5001/api/v1/ws/gesture

## 3. Navigation and Page Map
Main pages in the app:
- Vocabulary
- Chat Box
- Support
- Settings
- Logout

Use the floating menu button at the bottom-left corner to open the navigation panel.

## 4. Registration and Login
### 4.1 Register
1. Open the register page.
2. Enter full name, email, and password.
3. Click Create Account.

### 4.2 Login
1. Open the login page.
2. Enter email and password.
3. Click Login.
4. You will be redirected to the Vocabulary page after success.

### 4.3 Validation Rules
- Email must be valid (contains @)
- Password must have at least 6 characters
- Required fields cannot be empty

## 5. Vocabulary Page (Core Learning)
### 5.1 Key Areas
- Recognition rate bar (top)
- Category panel (left)
- Word grid and pagination
- Sign demonstration panel
- Your Sign camera panel
- Diagnostics panel (WebSocket / Health)

### 5.2 Practice Flow
1. Choose a category (or All Words).
2. Click a target word to enter demonstration view.
3. Watch the sign demonstration image.
4. Perform the sign in front of your camera.
5. When recognized sequence text matches the selected word, progress is saved and the word is marked completed.

### 5.3 Search and Pagination
- Search supports both Chinese and English keywords.
- The word list is paginated; use page controls at the bottom.

### 5.4 Diagnostics
Click Show Diagnostics / Hide Diagnostics to view:
- WebSocket status
- Health API status and latency
- Last message timestamps
- Error details (if any)

## 6. Chat Box and Sentence Generation
### 6.1 Key Areas
- Left panel: history search, session list, New Session
- Right panel: generation controls, message area, sign image strip, input area

### 6.2 Generate Sign-language Sentences
1. Click Generate Sign-language Sentence.
2. The app generates a normal sentence and a sign-expression line.
3. After conversation exists, the button changes to Continue Generate Sign-language Sentence.

### 6.3 Show or Hide Sign Images
- Click Show WebP Display to open the image strip.
- Click Hide WebP Display to collapse it.

### 6.4 Camera Input Mode
- Use the bottom-right mode button to switch between camera mode and keyboard mode.
- In camera mode, recognized text is fed into the input workflow.

### 6.5 Session History
- Create a New Session anytime.
- Click a session in the left panel to reload its messages.
- Use history search to filter sessions.

## 7. Support Page
This page provides hearing-impaired and sign-language related resources in Hong Kong, including:
- Major NGOs
- Government services
- Emergency support (for example 992 SMS)

Each resource card includes links, contact numbers, and descriptions.

## 8. Settings Page
### 8.1 Available Settings
- Account info (nickname, email)
- Color mode (light / dark)
- Font size (aa / Aa / AA)
- Accessibility (RG-CVD mode)
- Language (Traditional Chinese / English)

### 8.2 Save Changes
- A Save button appears after changes are made.
- Saved preferences persist across page reloads.

### 8.3 Logout
- Logout is available in both Settings and the floating navigation menu.

## 9. Troubleshooting
### 9.1 Black camera area or no recognition
- Confirm camera permission is granted.
- Refresh the page and retry.

### 9.2 Vocabulary page stuck at connecting
- Ensure gesture service is running with Python 3.10.
- Verify the Health endpoint is reachable.

### 9.3 Sign image strip is empty
- Confirm Show WebP Display is enabled.
- Some words may not have mapped image assets yet.

### 9.4 Sentence generation failed
- The model API may be rate-limited or temporarily unavailable.
- Retry after a short wait.

## 10. Recommended Onboarding Path
1. Open Settings first and adjust language and font size.
2. Practice one simple word in Vocabulary.
3. Verify camera recognition works, then move to Chat Box.
4. Use Support resources when external help is needed.

---
Version: v1 (based on current frontend behavior)
