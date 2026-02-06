 Quizfy 🎓
A backend-focused educational quiz management platform**

Quizfy is a full-stack web application designed to help teachers create, manage, and evaluate online quizzes while providing students with a secure, structured, and user-friendly assessment experience.

The system focuses on **real academic workflows**, including authentication, timed quizzes, automated evaluation, performance feedback, and Excel-based reporting.

---

 🚀 Key Features

 👩‍🏫 Teacher Features

* Create and manage quizzes
* Organize quizzes into folders
* Control quiz visibility and access
* Generate **QR codes** for quizzes
* View student submissions and results
* Export results as **Excel reports**

  * Individual student reports
  * Group / class-level reports
  * Report card–style exports

---

 👨‍🎓 Student Features

* Secure login required before accessing quizzes
* Scan a **QR code** to access a quiz page
* View quiz details:

  * Quiz name
  * Instructions
  * Timer (if enabled)
* Submit answers digitally
* Receive **immediate feedback** after submission:

  * Status such as:

    * **Failed**
    * **Needs Improvement**
    * (based on performance thresholds)
* View personal performance results

---

 🔐 Authentication & Security

* Separate authentication for teachers and students
* Login required before accessing any quiz
* CSRF protection enabled
* Passwords securely hashed using Django’s authentication system
* Sensitive configuration stored in environment variables (`.env`)
* `.env.example` included to demonstrate required variables without exposing secrets

---

 📱 QR-Based Quiz Access Flow

1. Teacher generates a quiz
2. System creates a **unique QR code**
3. Student scans the QR code
4. If not logged in → redirected to login
5. After login → quiz page opens
6. Student completes and submits the quiz
7. Result and status are shown immediately

This flow ensures **secure access** while keeping the experience simple for students.

---

 ⏱️ Quiz Experience

* Timed quizzes (when enabled)
* Clear submission flow
* Automatic evaluation
* Instant result display
* Performance status shown clearly to the student

---

 📤 Data Export & Reporting

Quizfy includes built-in tools for exporting academic data in **Excel format**, suitable for real educational use.

Supported Exports:

* **Single student report**

  * Quiz attempts
  * Score
  * Result status
* **Group / class report**

  * Multiple students in one spreadsheet
  * Useful for grading and analysis
* **Report card–style exports**

  * Structured format for academic records

All exports are generated **server-side** to ensure accuracy and consistency.

---

 🧱 Project Structure (Simplified)

```
Quizfy/
├── quizzes/              # Core quiz logic
├── quizz_app/            # Project configuration
├── scripts/              # Utility & maintenance scripts
│   ├── email/
│   ├── debug/
│   ├── maintenance/
│   └── helpbot/
├── templates/
├── media/
├── docs/                 # Documentation & guides
├── manage.py
├── requirements.txt
└── .env.example
```

---

 🛠️ Tech Stack

* **Backend:** Django (Python)
* **Frontend:** Django Templates (HTML, CSS, Bootstrap)
* **Database:** SQLite (development), production-ready configuration
* **Authentication:** Django Auth
* **Exports:** Excel generation (server-side)
* **Deployment:** Docker & Render-ready setup

---

 🧠 Design Philosophy

Quizfy was built with a strong focus on:

* Backend logic and data integrity
* Real academic workflows
* Security and access control
* Maintainable project structure
* Practical features used by teachers, not just demos

---

 ⚠️ Important Notes

* Virtual environments (`.venv`, `vv`) are excluded from version control
* Environment variables are never committed
* Utility scripts are organized under `scripts/` for clarity
* The project prioritizes **clarity and functionality** over unnecessary complexity

---

 📌 Future Improvements (Optional)

* Advanced analytics dashboards
* More granular performance categories
* Role-based permissions
* API layer for external integrations

---

 👤 Author

**Sara Al-Desouky**
Backend-focused Software Engineer
GitHub: [https://github.com/sara-aldesouky](https://github.com/sara-aldesouky)

