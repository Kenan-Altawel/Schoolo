# Automated School Management System  
**Open-source system to automate school operations (attendance, grading, communication, and analytics)**  

---

## 🚀 **Features**  
- 📝 Student Management (data, academic/behavior tracking)  
- 📅 Attendance via QR Code/Fingerprint + parent notifications  
- 📊 Dynamic Timetables & PDF Reports  
- 📱 Teacher-Parent Messaging & Event Alerts  

## 💻 **Tech Stack**  
- **Frontend**: React.js, Flutter  
- **Backend**: Django (Python)   
- **Database**: MySQL  
- **Tools**: Docker, GitHub Actions (CI/CD)  

---

## ⚡ Quick Start
Follow these steps to get the Django backend running locally:
- do make sure to have a MySQL server running and db created.

```bash
### 1. Clone the repository
git clone https://github.com/your-username/school-management-system.git

### 2. (Optional but recommended) Create and activate a virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

### 3. Install Python dependencies
pip install -r requirements.txt

### 4. Start server
python3 manage.py runserver
