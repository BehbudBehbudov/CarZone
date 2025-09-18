# CarZone 

**CarZone** is a Django REST Framework–based backend project for managing car listings.  
It includes advanced features like authentication, filtering, comments, real-time chat, and admin-only category management.

---

## Features

- **User Authentication**
  - JWT Authentication for login & registration  
  - Basic Token for logout  
  - 3-step password reset system (request, verify, confirm)  

- **Car Management**
  - CRUD operations for Cars, Authors, and Categories  
  - Image upload support for car listings  
  - Extended fields for detailed filtering  

- **Comments**
  - Users can post comments under car listings  
  - Update & delete own comments  

- **Favorites**
  - Add or remove cars from favorites list  

- **Search & Filtering**
  - Search by name, content, and category  
  - Advanced filtering by all car model fields  

- **Admin Control**
  - Only superadmins can add categories  

- **Real-Time Chat 💬**
  - WebSocket-based private chat system using Django Channels  
  - Send, edit, delete, and revoke messages  
  - Block users from messaging  
  - Read receipts (seen/unseen)  

- **Notifications 🔔**
  - WebSocket push notifications for new messages  

- **Documentation**
  - Swagger UI at `/swagger/`  
  - ReDoc documentation at `/redoc/`  

---

##  Tech Stack

- **Backend:** Django, Django REST Framework  
- **Auth:** JWT, Basic Authentication  
- **Database:** SQLite (for demo), compatible with PostgreSQL/MySQL  
- **Realtime:** Django Channels (WebSocket)  
- **Tools:** Swagger, ReDoc  

---

##  Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/CarZone.git
cd CarZone

# Create virtual environment
python -m venv venv
source venv/bin/activate   # (Linux/Mac)
venv\Scripts\activate      # (Windows)

# Install dependencies
pip install -r requirements.txt

# Set environment variables in .env
SECRET_KEY=your_secret_key
DEBUG=True
DATABASE_URL=sqlite:///db.sqlite3

# Run migrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# Run the server
python manage.py runserver
