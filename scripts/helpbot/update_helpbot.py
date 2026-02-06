#!/usr/bin/env python
"""Script to update the Teacher Help Bot section in views.py"""

NEW_HELPBOT_SECTION = '''# --- Smart Teacher Help Bot (Comprehensive FAQ + AI-like matching) ---

TEACHER_KB = [
    # ========== FOLDERS & ORGANIZATION ==========
    {
        "tags": ["create folder", "subject folder", "add subject", "new folder", "folder", "make folder"],
        "q": "How do I create a subject folder?",
        "a": (
            "📁 **Creating a Subject Folder:**\\n\\n"
            "1. Go to your **Dashboard** (My Subjects)\\n"
            "2. Click **+ Create Subject Folder**\\n"
            "3. Enter the folder name (e.g., Physics, Math 101)\\n"
            "4. Click **Save**\\n\\n"
            "💡 Tip: Organize your quizzes by subject or course for easy management!"
        )
    },
    {
        "tags": ["move quiz", "assign quiz", "put quiz in folder", "organize quizzes", "ungrouped", "move to folder"],
        "q": "How do I move a quiz into a folder?",
        "a": (
            "📦 **Moving a Quiz to a Folder:**\\n\\n"
            "1. Find the quiz in **Ungrouped Quizzes** section\\n"
            "2. Click the **Move** button\\n"
            "3. Select the destination folder\\n"
            "4. Click **Save**\\n\\n"
            "💡 You can also move quizzes between folders the same way!"
        )
    },
    {
        "tags": ["delete folder", "remove folder", "folder delete"],
        "q": "How do I delete a folder?",
        "a": (
            "🗑️ **Deleting a Folder:**\\n\\n"
            "1. Click the **🗑️** button on the folder card\\n"
            "2. Choose what to do with quizzes inside:\\n"
            "   • **Delete All**: Removes folder AND all quizzes\\n"
            "   • **Move to Ungrouped**: Keeps quizzes, deletes only folder\\n\\n"
            "⚠️ Warning: Deleting quizzes will also delete all student submissions!"
        )
    },
    
    # ========== QUIZ CREATION ==========
    {
        "tags": ["create quiz", "new quiz", "make quiz", "add quiz"],
        "q": "How do I create a quiz?",
        "a": (
            "📝 **Creating a New Quiz:**\\n\\n"
            "1. Click **+ Create Quiz** (on dashboard or inside a folder)\\n"
            "2. Enter the quiz **Title**\\n"
            "3. Select **Quiz Type**:\\n"
            "   • Multiple Choice\\n"
            "   • True/False\\n"
            "   • File Upload (students submit PDFs/images)\\n"
            "4. Optionally assign to a folder\\n"
            "5. Set **Duration** (in minutes) if timed\\n"
            "6. Click **Create**\\n\\n"
            "💡 After creating, add questions from the quiz detail page!"
        )
    },
    {
        "tags": ["add question", "create question", "new question", "questions"],
        "q": "How do I add questions to a quiz?",
        "a": (
            "❓ **Adding Questions:**\\n\\n"
            "1. Open the quiz (click **Open**)\\n"
            "2. Click **+ Add Question**\\n"
            "3. Choose question type:\\n"
            "   • **Multiple Choice**: 4 options, select correct one\\n"
            "   • **True/False**: Just enter the statement\\n"
            "   • **File Upload**: Students upload their answer as PDF/image\\n"
            "4. Enter the question text\\n"
            "5. Add an image (optional)\\n"
            "6. Click **Save**\\n\\n"
            "💡 You can mix different question types in the same quiz!"
        )
    },
    {
        "tags": ["edit question", "change question", "modify question", "update question"],
        "q": "How do I edit a question?",
        "a": (
            "✏️ **Editing Questions:**\\n\\n"
            "1. Open the quiz\\n"
            "2. Find the question you want to edit\\n"
            "3. Click the **Edit** button\\n"
            "4. Make your changes\\n"
            "5. Click **Save**\\n\\n"
            "⚠️ Note: Editing after students have submitted may affect their results!"
        )
    },
    {
        "tags": ["delete question", "remove question"],
        "q": "How do I delete a question?",
        "a": (
            "🗑️ **Deleting Questions:**\\n\\n"
            "1. Open the quiz\\n"
            "2. Find the question\\n"
            "3. Click the **Delete** button\\n"
            "4. Confirm deletion\\n\\n"
            "⚠️ Warning: This will also delete all student answers for that question!"
        )
    },
    {
        "tags": ["quiz type", "file upload quiz", "multiple choice quiz", "true false quiz", "quiz types", "type of quiz"],
        "q": "What quiz types are available?",
        "a": (
            "📋 **Available Quiz Types:**\\n\\n"
            "**1. Multiple Choice**\\n"
            "   • 4 options per question\\n"
            "   • Auto-graded instantly\\n\\n"
            "**2. True/False**\\n"
            "   • Simple yes/no questions\\n"
            "   • Auto-graded instantly\\n\\n"
            "**3. File Upload**\\n"
            "   • Students upload PDF, JPG, or PNG\\n"
            "   • You grade manually with comments\\n"
            "   • Great for essays, drawings, handwritten work\\n\\n"
            "💡 You can also mix question types within a quiz!"
        )
    },
    
    # ========== QUIZ SETTINGS ==========
    {
        "tags": ["quiz settings", "timer", "duration", "time limit", "timed quiz", "minutes"],
        "q": "How do I set a time limit for a quiz?",
        "a": (
            "⏱️ **Setting a Time Limit:**\\n\\n"
            "1. Open the quiz\\n"
            "2. Click **⚙️ Settings**\\n"
            "3. Enter **Duration** in minutes\\n"
            "4. Click **Save**\\n\\n"
            "How it works:\\n"
            "• Timer starts when student opens the quiz\\n"
            "• Auto-submits when time runs out\\n"
            "• Students see countdown on their screen\\n\\n"
            "💡 Leave blank for unlimited time!"
        )
    },
    {
        "tags": ["due date", "deadline", "quiz expires", "end date", "close date"],
        "q": "How do I set a due date for a quiz?",
        "a": (
            "📅 **Setting a Due Date:**\\n\\n"
            "1. Open the quiz\\n"
            "2. Click **⚙️ Settings**\\n"
            "3. Set the **Due Date/Time**\\n"
            "4. Click **Save**\\n\\n"
            "After the due date:\\n"
            "• Quiz automatically closes\\n"
            "• Students cannot submit anymore\\n"
            "• Existing submissions are saved"
        )
    },
    {
        "tags": ["start quiz", "stop quiz", "activate", "deactivate", "toggle", "close quiz", "open quiz", "active"],
        "q": "How do I start or stop a quiz?",
        "a": (
            "🔄 **Starting/Stopping a Quiz:**\\n\\n"
            "1. Open the quiz\\n"
            "2. Click the **Start Quiz** or **Stop Quiz** button\\n\\n"
            "**When Active (Started):**\\n"
            "• Students can access and submit\\n"
            "• Shows green indicator\\n\\n"
            "**When Inactive (Stopped):**\\n"
            "• Students see 'Quiz Closed' message\\n"
            "• No new submissions allowed\\n"
            "• You can review existing submissions\\n\\n"
            "💡 Great for controlling when students can take the quiz!"
        )
    },
    
    # ========== QUIZ CODE & SHARING ==========
    {
        "tags": ["quiz code", "share code", "where is code", "find code", "code", "share quiz"],
        "q": "Where do I find the quiz code?",
        "a": (
            "🔑 **Finding the Quiz Code:**\\n\\n"
            "The code is shown on:\\n"
            "• Quiz card: **Code: ABC123**\\n"
            "• Quiz detail page header\\n\\n"
            "**Sharing with Students:**\\n"
            "• Tell them the code verbally\\n"
            "• Write it on the board\\n"
            "• Share via class group\\n"
            "• Use the QR code feature!\\n\\n"
            "Students enter this code on their dashboard to access the quiz."
        )
    },
    {
        "tags": ["qr code", "scan", "qr", "barcode", "scan code"],
        "q": "How do I use the QR code feature?",
        "a": (
            "📱 **Using QR Codes:**\\n\\n"
            "1. Open the quiz\\n"
            "2. Click **Show QR Code**\\n"
            "3. Display it on screen/projector\\n"
            "4. Students scan with their phone camera\\n\\n"
            "Benefits:\\n"
            "• No typing quiz code\\n"
            "• Fast classroom access\\n"
            "• Works with any QR scanner app\\n\\n"
            "💡 Students will be prompted to log in if not already!"
        )
    },
    
    # ========== STUDENTS & SUBMISSIONS ==========
    {
        "tags": ["student access", "login", "account required", "solve quiz", "student account", "student signup"],
        "q": "Can students access quizzes without an account?",
        "a": (
            "👤 **Student Account Requirements:**\\n\\n"
            "No, students MUST create an account and log in.\\n\\n"
            "**Student Sign Up Process:**\\n"
            "1. Go to the app homepage\\n"
            "2. Click **Student Sign Up**\\n"
            "3. Fill in their details:\\n"
            "   • Name, University ID\\n"
            "   • Major, Section, City\\n"
            "4. Create username & password\\n\\n"
            "This allows tracking individual submissions and grades."
        )
    },
    {
        "tags": ["view submissions", "see answers", "student responses", "results", "grades", "submissions"],
        "q": "How do I view student submissions?",
        "a": (
            "📊 **Viewing Submissions:**\\n\\n"
            "1. Open the quiz\\n"
            "2. Click **View Submissions**\\n"
            "3. See list of all students who submitted\\n\\n"
            "For each submission you can see:\\n"
            "• Student name & ID\\n"
            "• Score (auto-graded questions)\\n"
            "• Submission time\\n"
            "• Click to view detailed answers\\n\\n"
            "💡 Click **View & Grade** to grade file uploads!"
        )
    },
    {
        "tags": ["grade", "grading", "file upload grade", "mark", "score file", "grade file", "feedback"],
        "q": "How do I grade file upload submissions?",
        "a": (
            "✏️ **Grading File Uploads:**\\n\\n"
            "1. Open quiz → **View Submissions**\\n"
            "2. Click **View & Grade** on a submission\\n"
            "3. Click **👁️ Preview** to view the student's file\\n"
            "4. Enter a **Grade** (e.g., A, B+, 85%)\\n"
            "5. Add **Feedback Comments**\\n"
            "6. Optionally upload a **Corrected File**\\n"
            "7. Click **💾 Save Grading**\\n\\n"
            "Students will see your grade and feedback on their dashboard!"
        )
    },
    {
        "tags": ["extra attempt", "retry", "retake", "another try", "allow retry", "more attempts"],
        "q": "How do I allow a student to retake a quiz?",
        "a": (
            "🔄 **Allowing Extra Attempts:**\\n\\n"
            "1. Open quiz → **View Submissions**\\n"
            "2. Find the student\\n"
            "3. Click **Allow Extra Attempt**\\n\\n"
            "This gives them one more try. You can click multiple times for more attempts.\\n\\n"
            "💡 Useful for students who had technical issues!"
        )
    },
    
    # ========== EXPORT & REPORTS ==========
    {
        "tags": ["export", "excel", "download", "submissions file", "xlsx", "spreadsheet", "download grades"],
        "q": "How do I export submissions to Excel?",
        "a": (
            "📥 **Exporting to Excel:**\\n\\n"
            "**Option 1: Single Quiz**\\n"
            "• Open quiz → Click **Export Excel**\\n\\n"
            "**Option 2: Entire Folder**\\n"
            "• On folder card → Click **📥 Export**\\n\\n"
            "The Excel file includes:\\n"
            "• Student full name\\n"
            "• University ID\\n"
            "• Section\\n"
            "• Score/Grade\\n"
            "• Submission time\\n\\n"
            "💡 Great for uploading to your university's grading system!"
        )
    },
    {
        "tags": ["analytics", "statistics", "performance", "weak topics", "ai analysis", "reports"],
        "q": "How do I see analytics and weak topics?",
        "a": (
            "📈 **Learning Analytics:**\\n\\n"
            "1. Open a **Subject Folder**\\n"
            "2. Click **📊 Analytics**\\n\\n"
            "You'll see:\\n"
            "• Most difficult questions (high error rates)\\n"
            "• Student performance overview\\n"
            "• AI-powered topic analysis\\n\\n"
            "Click **Analyze with AI** to get:\\n"
            "• Weak topic identification\\n"
            "• Root cause analysis\\n"
            "• Teaching recommendations\\n\\n"
            "💡 Requires OpenAI API key in settings!"
        )
    },
    
    # ========== ACCOUNT & SECURITY ==========
    {
        "tags": ["change password", "password", "security", "update password", "new password"],
        "q": "How do I change my password?",
        "a": (
            "🔐 **Changing Your Password:**\\n\\n"
            "1. Click **Change Password** (top of dashboard)\\n"
            "2. Enter your current password\\n"
            "3. Enter new password (twice)\\n"
            "4. Click **Change Password**\\n\\n"
            "💡 Use a strong password with letters, numbers, and symbols!"
        )
    },
    {
        "tags": ["logout", "sign out", "log out"],
        "q": "How do I log out?",
        "a": (
            "👋 **Logging Out:**\\n\\n"
            "Click the **Logout** link in the navigation.\\n\\n"
            "💡 Always log out when using shared computers!"
        )
    },
    
    # ========== TROUBLESHOOTING ==========
    {
        "tags": ["student can't access", "student problem", "quiz not working", "error", "issue", "problem"],
        "q": "A student can't access the quiz. What should I check?",
        "a": (
            "🔧 **Troubleshooting Student Access:**\\n\\n"
            "Check these things:\\n\\n"
            "1. **Is the quiz active?**\\n"
            "   • Make sure you clicked Start Quiz\\n\\n"
            "2. **Has the due date passed?**\\n"
            "   • Check quiz settings\\n\\n"
            "3. **Did they use the correct code?**\\n"
            "   • Codes are case-insensitive\\n\\n"
            "4. **Are they logged in?**\\n"
            "   • Students need an account\\n\\n"
            "5. **Have they already submitted?**\\n"
            "   • Default is 1 attempt - allow extra if needed"
        )
    },
    {
        "tags": ["missing submission", "didn't submit", "lost answers", "no submission"],
        "q": "A student says they submitted but I don't see it?",
        "a": (
            "🔍 **Finding Missing Submissions:**\\n\\n"
            "1. Check the submissions list carefully (sorted by time)\\n"
            "2. The student may have:\\n"
            "   • Started but not clicked Submit\\n"
            "   • Had internet issues\\n"
            "   • Used a different account\\n\\n"
            "**Solutions:**\\n"
            "• Allow an extra attempt for them\\n"
            "• Have them try again\\n"
            "• Check if timer auto-submitted (shows in submission time)"
        )
    },
    
    # ========== TIPS & BEST PRACTICES ==========
    {
        "tags": ["tips", "best practices", "advice", "help", "how to use", "guide"],
        "q": "Any tips for using Quizfy effectively?",
        "a": (
            "💡 **Pro Tips:**\\n\\n"
            "**Organization:**\\n"
            "• Create folders by subject/course\\n"
            "• Use clear quiz titles with dates\\n\\n"
            "**Quizzes:**\\n"
            "• Test your quiz before sharing\\n"
            "• Use QR codes for fast access\\n"
            "• Set appropriate time limits\\n\\n"
            "**Grading:**\\n"
            "• Export to Excel regularly\\n"
            "• Use analytics to find weak areas\\n"
            "• Provide detailed feedback on file uploads\\n\\n"
            "**Students:**\\n"
            "• Share the code clearly\\n"
            "• Remind them to click Submit!"
        )
    },
    {
        "tags": ["hello", "hi", "hey", "greetings"],
        "q": "Hello",
        "a": (
            "👋 **Hello!** I'm your Quizfy Assistant.\\n\\n"
            "I can help you with:\\n"
            "• Creating and managing quizzes\\n"
            "• Organizing subject folders\\n"
            "• Grading student submissions\\n"
            "• Exporting grades to Excel\\n"
            "• Using analytics features\\n\\n"
            "Just ask me a question!"
        )
    },
    {
        "tags": ["thank", "thanks", "thank you"],
        "q": "Thank you",
        "a": (
            "😊 You're welcome! Happy to help.\\n\\n"
            "If you have more questions, just ask!"
        )
    },
]

def _normalize(text: str) -> str:
    text = (text or "").lower().strip()
    text = re.sub(r"\\s+", " ", text)
    return text

def _score_match(query: str, item: dict) -> float:
    """Score how well a query matches a KB item"""
    query_norm = _normalize(query)
    query_words = set(query_norm.split())
    
    # Remove common filler words for matching
    filler_words = {"the", "a", "an", "is", "are", "can", "i", "you", "how", "do", "to", "my", "this", "that", "what", "where", "when", "please", "help", "want", "need"}
    query_words = query_words - filler_words
    
    score = 0.0
    
    # Check tags (highest priority)
    for tag in item["tags"]:
        tag_norm = _normalize(tag)
        tag_words = set(tag_norm.split()) - filler_words
        
        # Exact tag match in query
        if tag_norm in query_norm:
            score += 15.0
        
        # Query contains tag
        if query_norm in tag_norm:
            score += 10.0
        
        # Word overlap
        overlap = len(query_words & tag_words)
        if overlap > 0:
            score += overlap * 3.0
    
    # Check question text
    q_norm = _normalize(item["q"])
    q_words = set(q_norm.split()) - filler_words
    overlap = len(query_words & q_words)
    score += overlap * 2.0
    
    # Fuzzy matching for typos
    for qw in query_words:
        if len(qw) < 3:
            continue
        for tag in item["tags"]:
            tag_words = _normalize(tag).split()
            matches = difflib.get_close_matches(qw, tag_words, n=1, cutoff=0.75)
            if matches:
                score += 2.0
    
    return score

def _best_answer(message: str) -> str:
    msg = message.strip()
    
    if not msg:
        return "👋 Hi! Ask me anything about using Quizfy. For example:\\n• How do I create a quiz?\\n• How do I grade submissions?\\n• How do I export to Excel?"
    
    # Score all KB items
    scores = []
    for item in TEACHER_KB:
        score = _score_match(msg, item)
        if score > 0:
            scores.append((score, item))
    
    # Sort by score (highest first)
    scores.sort(key=lambda x: x[0], reverse=True)
    
    if scores and scores[0][0] >= 3.0:
        return scores[0][1]["a"]
    
    # Fallback with suggestions
    return (
        "🤔 I'm not sure about that. Here are some things I can help with:\\n\\n"
        "**Quizzes:**\\n"
        "• How do I create a quiz?\\n"
        "• How do I add questions?\\n"
        "• How do I set a time limit?\\n\\n"
        "**Grading:**\\n"
        "• How do I view submissions?\\n"
        "• How do I grade file uploads?\\n"
        "• How do I export to Excel?\\n\\n"
        "**Organization:**\\n"
        "• How do I create folders?\\n"
        "• How do I use analytics?\\n\\n"
        "Try asking one of these questions!"
    )

'''

# Read the file
with open('quizzes/views.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Find start and end of the section
start_marker = '# --- Teacher Help Bot (FAQ + fuzzy match) ---'
end_marker = '@staff_required\n@require_POST\ndef teacher_help_bot(request):'

start = content.find(start_marker)
end = content.find(end_marker)

if start == -1:
    print("ERROR: Could not find start marker")
elif end == -1:
    print("ERROR: Could not find end marker")
else:
    # Replace the section
    new_content = content[:start] + NEW_HELPBOT_SECTION + content[end:]
    
    with open('quizzes/views.py', 'w', encoding='utf-8') as f:
        f.write(new_content)
    
    print("SUCCESS: Updated teacher help bot section!")
    print(f"Replaced {end - start} chars with {len(NEW_HELPBOT_SECTION)} chars")
