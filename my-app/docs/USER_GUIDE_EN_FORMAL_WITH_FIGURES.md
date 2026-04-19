# Sign Language Learning Platform
# User Manual (Formal Edition | With Figure Index)

Document ID: FYP-SL-UG-EN-002  
Version: v2.0  
Language: English  
Date: 2026-04-19  
Scope: Web Frontend (my-app)

---

## Document Control
![Figure: Document Control](./figures/shared/section-00-document-control.png)

### Revision History
![Figure: Revision History](./figures/shared/section-00-revision-history.png)

| Version | Date | Author | Summary |
|---|---|---|---|
| v1.0 | 2026-04-19 | Copilot | Initial practical user guide |
| v2.0 | 2026-04-19 | Copilot | Formal structure and figure numbering reference |

### Purpose
![Figure: Purpose](./figures/shared/section-00-purpose.png)

This manual provides standardized operating instructions for:
- user onboarding and training,
- demo and presentation support,
- delivery and maintenance reference.

### Target Audience
![Figure: Target Audience](./figures/shared/section-00-target-audience.png)

- End users
- QA / testing members
- Trainers and presenters

---

## Table of Contents
![Figure: Table of Contents](./figures/shared/section-00-table-of-contents.png)

1. System Overview  
2. Prerequisites  
3. Navigation and Page Map  
4. Registration and Login  
5. Vocabulary Learning and Gesture Recognition  
6. Chat Box and Sentence Generation  
7. Support Resources  
8. Settings  
9. Troubleshooting  
10. Standard Operating Procedures (SOP)  
11. Appendix (APIs and Local Settings)

---

## 1. System Overview
![Figure: 1. System Overview](./figures/shared/section-01-system-overview.png)

The platform combines vocabulary learning, live gesture recognition, AI sentence generation, support resource lookup, and personalized settings.

Core capabilities:
- categorized sign vocabulary learning,
- real-time camera-based gesture recognition (WebSocket),
- AI-generated sentence and sign-expression output,
- support directory (NGO/government/emergency),
- accessibility and appearance controls.

---

## 2. Prerequisites
![Figure: 2. Prerequisites](./figures/shared/section-02-prerequisites.png)

### 2.1 Environment
![Figure: 2.1 Environment](./figures/shared/section-02-1-environment.png)

- Browser: Chrome recommended
- Device: camera access required for practice
- Network: backend APIs must be reachable

### 2.2 Gesture Service Startup (if needed)
![Figure: 2.2 Gesture Service Startup (if needed)](./figures/shared/section-02-2-gesture-service-startup.png)

If the vocabulary page stays in connecting/offline state, run the gesture backend:

```bash
py -3.10 app_simple.py
```

Run it in the cv_hands directory when possible.  
Default endpoints:
- Health: http://127.0.0.1:5001/api/v1/health
- WebSocket: ws://127.0.0.1:5001/api/v1/ws/gesture

---

## 3. Navigation and Page Map
![Figure: 3. Navigation and Page Map](./figures/shared/section-03-navigation-page-map.png)

Main pages:
- Vocabulary
- Chat Box
- Support
- Settings
- Logout

Navigation behavior:
- Open/close the floating menu from the bottom-left button.
- Select a nav item to route to the target page.

---

## 4. Registration and Login
![Figure: 4. Registration and Login](./figures/shared/section-04-registration-login.png)

### 4.1 Register
![Figure: 4.1 Register](./figures/shared/section-04-1-register.png)

1. Open the Register page.
2. Enter full name, email, and password.
3. Click Create Account.

### 4.2 Login
![Figure: 4.2 Login](./figures/shared/section-04-2-login.png)

1. Open the Login page.
2. Enter email and password.
3. Click Login.
4. On success, user is redirected to Vocabulary.

### 4.3 Validation Rules
![Figure: 4.3 Validation Rules](./figures/shared/section-04-3-validation-rules.png)

- Email must be valid (contains @)
- Password minimum length: 6
- Required fields cannot be empty

---

## 5. Vocabulary Learning and Gesture Recognition
![Figure: 5. Vocabulary Learning and Gesture Recognition](./figures/shared/section-05-vocabulary-learning.png)

### 5.1 Functional Areas
![Figure: 5.1 Functional Areas](./figures/shared/section-05-1-functional-areas.png)

- recognition rate bar,
- category panel and word list,
- search and pagination,
- sign demonstration panel,
- live camera panel,
- diagnostics panel.

### 5.2 Practice Steps
![Figure: 5.2 Practice Steps](./figures/shared/section-05-2-practice-steps.png)

1. Choose a category (or All Words).
2. Select a target word.
3. Review the sign demonstration image.
4. Perform the sign in front of camera.
5. System compares recognized sequence text with selected word.
6. On match, progress is saved and completion is marked.

### 5.3 Diagnostics
![Figure: 5.3 Diagnostics](./figures/shared/section-05-3-diagnostics.png)

Toggle Show Diagnostics / Hide Diagnostics to inspect:
- WebSocket status,
- Health API status and latency,
- last message timestamps,
- current error details.

---

## 6. Chat Box and Sentence Generation
![Figure: 6. Chat Box and Sentence Generation](./figures/shared/section-06-chat-sentence-generation.png)

### 6.1 Functional Areas
![Figure: 6.1 Functional Areas](./figures/shared/section-06-1-functional-areas.png)

- Left: session history, search, New Session
- Right: generation controls, chat thread, sign-image strip, input controls

### 6.2 Operation Steps
![Figure: 6.2 Operation Steps](./figures/shared/section-06-2-operation-steps.png)

1. Click Generate Sign-language Sentence.
2. The app returns a normal sentence and a sign-expression line.
3. Continue with Continue Generate Sign-language Sentence.
4. Click Show WebP Display to open sign images.
5. Click Hide WebP Display to collapse the strip.
6. Switch between camera mode and keyboard mode as needed.

### 6.3 Session Management
![Figure: 6.3 Session Management](./figures/shared/section-06-3-session-management.png)

- Create a New Session any time.
- Select historical sessions from the left panel.
- Filter sessions with the history search box.

---

## 7. Support Resources
![Figure: 7. Support Resources](./figures/shared/section-07-support-resources.png)

The Support page includes:
- major NGOs,
- government service links,
- emergency support information.

Each card provides website URLs, contact numbers, and service descriptions.

---

## 8. Settings
![Figure: 8. Settings](./figures/shared/section-08-settings.png)

### 8.1 Configurable Items
![Figure: 8.1 Configurable Items](./figures/shared/section-08-1-configurable-items.png)

- account info (read-only display),
- color mode (light/dark),
- font size (aa/Aa/AA),
- accessibility (RG-CVD mode),
- language (Traditional Chinese/English).

### 8.2 Save and Logout
![Figure: 8.2 Save and Logout](./figures/shared/section-08-2-save-logout.png)

- Save button appears after changes are made.
- Logout is available in both Settings and floating navigation.

---

## 9. Troubleshooting
![Figure: 9. Troubleshooting](./figures/shared/section-09-troubleshooting.png)

### 9.1 Camera is black or not recognizing
![Figure: 9.1 Camera is black or not recognizing](./figures/shared/section-09-1-camera-issue.png)

- Confirm browser camera permission.
- Refresh page and retry.

### 9.2 Vocabulary page stuck in connecting
![Figure: 9.2 Vocabulary page stuck in connecting](./figures/shared/section-09-2-connecting-issue.png)

- Ensure Python 3.10 gesture service is running.
- Verify health endpoint connectivity.

### 9.3 No sign images shown
![Figure: 9.3 No sign images shown](./figures/shared/section-09-3-sign-images-missing.png)

- Confirm Show WebP Display is enabled.
- Some words may not yet have mapped image assets.

### 9.4 Sentence generation failed
![Figure: 9.4 Sentence generation failed](./figures/shared/section-09-4-generation-failed.png)

- Model API may be rate-limited or temporarily unavailable.
- Retry after a short delay.

---

## 10. Standard Operating Procedures (SOP)
![Figure: 10. Standard Operating Procedures (SOP)](./figures/shared/section-10-sop.png)

### SOP-01 First-time User Onboarding
![Figure: SOP-01 First-time User Onboarding](./figures/shared/section-10-sop-01-first-time-user-onboarding.png)

1. Register an account.
2. Log in and open Vocabulary page.
3. Configure language, theme, and font size in Settings.
4. Complete at least one vocabulary recognition.
5. Generate at least one sentence in Chat Box.

### SOP-02 Classroom / Demo Flow
![Figure: SOP-02 Classroom / Demo Flow](./figures/shared/section-10-sop-02-classroom-demo-flow.png)

1. Demonstrate categories, search, and pagination in Vocabulary.
2. Demonstrate live camera recognition and matching.
3. Demonstrate sentence generation and sign-image display in Chat Box.
4. Demonstrate support lookup from Support page.

### SOP-03 Incident Diagnosis Flow
![Figure: SOP-03 Incident Diagnosis Flow](./figures/shared/section-10-sop-03-incident-diagnosis-flow.png)

1. Open Diagnostics in Vocabulary.
2. Check WebSocket and Health status.
3. Confirm Python 3.10 backend process is running.
4. Refresh and retest.

---

## 11. Appendix (APIs and Local Settings)
![Figure: 11. Appendix (APIs and Local Settings)](./figures/shared/section-11-appendix.png)

### 11.1 Key APIs
![Figure: 11.1 Key APIs](./figures/shared/section-11-1-key-apis.png)

- login.php
- get_words.php
- get_webp_for_words.php
- save_progress.php
- get_user_progress.php
- save_chat.php
- get_chat_sessions.php
- get_chat_history.php
- /api/v1/ws/gesture
- /api/v1/health

### 11.2 Common localStorage Keys
![Figure: 11.2 Common localStorage Keys](./figures/shared/section-11-2-localstorage-keys.png)

- isAuthenticated
- user / userId / userName
- language
- colorMode
- rgCvdMode
- fontSize
- chatSessionId

---

End of document