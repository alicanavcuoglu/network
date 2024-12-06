# Social50

## Video Demo: [Social50](https://www.youtube.com/watch?v=A4_RpUCb9n8&ab_channel=AlicanAvcuoglu)

## Description:

This is Social50, a web-based application designed to connect CS50 students with shared interests. Social50 aims to unite CS50 students and serve as a native platform for fostering a vibrant community of learners and collaborators.

My hope is that fellow CS50 students will find value in connecting with peers, sharing experiences, and building lasting relationships within the community. Through Social50, we can create a supportive environment where students can collaborate, learn from each other, and grow together in their programming journey.

## Overview

Social50 facilitates meaningful connections and interactions through a comprehensive suite of features:

- **Feed**: Share updates, insights, and learning experiences.
- **Interact Users**: Interact with users by liking, commenting, or resharing their posts.
- **Friend Network**: Build your personal network within the CS50 community.
- **Direct Messaging**: Connect one-on-one with fellow students.
- **Group Discussions**: Join and participate in various interest-based groups.
- **Notifications**: Stay updated on relevant activities and interactions.
- **Real-Time Updates**: Receive messages and notifications in real-time, ensuring you're always connected and up to date.

## Key Features

### 1. User Registration and Authentication

- Passwords hashed with Werkzeug for secure storage.

### 2. Profiles

- Customizable profiles featuring profile pictures, bios, classes and interests.
- Display of friend lists and pending friend requests.

### 3. Groups

- Interest-based groups.
- Owner, admin, and member hierarchy.

### 4. Messaging

- Real-time messaging powered by Flask-SocketIO.
- Notification indicators for unread messages.

### 5. Requests

- Viewing & sending friend requests.
- Viewing & sending group requests.

### 6. Notifications

- Users receive instant notifications for:
  - Friend requests and approvals.
  - New messages (Seperate from notifications dropdown).
  - Post interactions, including likes, comments, and shares.
  - Group invitations, admin promotions, group invitation approvals.
- Notifications are displayed in a dropdown accessible from the navbar.
- Unread notifications are highlighted for clarity.

### 7. Post Sharing

- Users can create and share posts.
- Posts support interactions such as likes, comments and reshares.

### 8. Search and Filter

- Users can search for peers based on name.
- Tags allow filtering posts with specific tags.

### 9. Pagination

- Seamless navigation through large datasets using paginated views.
- Pagination is implemented for:
   - Posts on the user feed.
   - Search results for posts, users, and groups.
   - Notifications and friend requests.

### 10. Responsive Design

- Optimized for desktop and mobile devices.
- Developed using Bootstrap for a consistent and attractive UI.

## Goals

The primary goals of Social50 are:

- Become a native platform for CS50 students & alumnis that is developed and maintained by the community itself
- Foster meaningful connections between users with shared interests
- Provide tools for seamless communication, enhancing users' learning journeys, careers, and experiences.
- Build a supportive environment where users can freely discuss their challenges, achievements, and knowledge
- Create lasting relationships that extend beyond the course duration

## Technologies Used

### Backend

**Flask**: A lightweight Python framework for web development.

**SQLite (previous) and PostgreSQL (current)**: Database systems.

### Frontend

**HTML, CSS, and JavaScript** for structuring and styling.

**Bootstrap**: Framework for responsive design.

**Jinja2**: Templating engine to dynamically render data.

### Deployment & Hosting
On process..

### Libraries

**Werkzeug**: For secure password hashing.

**Flask-SocketIO**: For real-time messaging.

**Flask-SQLAlchemy**: ORM for database operations.

**Flask-Migrate**: For database migrations.

**Flask-Session**: For session management.

**requests**: For making HTTP requests.

**python-dotenv**: For managing environment variables.

**psycopg2-binary**: For PostgreSQL database connectivity.

**Enum**: For specific values.

**pytz**: For timezone management.

**boto3**: For AWS integrations.

## Challenges Faced

### 1. Real-Time Messaging

Initially, implementing real-time messaging without using Socket.IO rooms proved complex. The solution involved directly emitting messages to user-specific session IDs.

### 2. Scroll Position Preservation

Maintaining scroll position when loading older messages was another challenge. This was resolved by using a temporary marker div to stabilize the scroll view.

### 3. Notifications System

Integrating a dropdown notification system with global accessibility required restructuring JavaScript files and ensuring a clean separation of logic.

### 4. Deployment

Transitioning from SQLite to PostgreSQL during deployment required several database adjustments and testing.

## Security Measures

- All sensitive data, including passwords, are hashed and stored securely.
- User input is sanitized to prevent SQL injection and XSS attacks.
- HTTPS is enforced in the production environment to ensure secure communication.

## Project Structure

```
├── app
│   ├── __init__.py
│   ├── config.py
│   ├── events.py
│   ├── extensions.py
│   ├── handlers.py
│   ├── models.py
│   ├── routes
│   │   ├── __init__.py
│   │   ├── auth_routes.py
│   │   ├── error_routes.py
│   │   ├── filter_routes.py
│   │   ├── group_routes.py
│   │   └── main_routes.py
│   ├── services
│   │   ├── __init__.py
│   │   ├── messages.py
│   │   ├── notifications.py
│   │   └── queries.py
│   ├── static
│   │   ├── group_placeholder.jpg
│   │   ├── js
│   │   │   ├── feed.js
│   │   │   ├── notifications.js
│   │   │   └── userActions.js
│   │   ├── placeholder.jpg
│   │   └── styles.css
│   ├── templates
│   │   ├── auth
│   │   │   ├── complete.html
│   │   │   ├── email_confirmation.html
│   │   │   ├── login.html
│   │   │   └── register.html
│   │   ├── components
│   │   │   ├── group_actions.html
│   │   │   ├── group_card.html
│   │   │   ├── group_cover.html
│   │   │   ├── post.html
│   │   │   ├── user_actions.html
│   │   │   ├── user_card.html
│   │   │   └── user_cover.html
│   │   ├── errors
│   │   │   ├── 400.html
│   │   │   ├── 401.html
│   │   │   ├── 404.html
│   │   │   ├── 413.html
│   │   │   ├── 422.html
│   │   │   └── 500.html
│   │   ├── feed.html
│   │   ├── groups
│   │   │   ├── create.html
│   │   │   ├── group
│   │   │   │   ├── about.html
│   │   │   │   ├── all_admins.html
│   │   │   │   ├── all_members.html
│   │   │   │   ├── index.html
│   │   │   │   ├── invite.html
│   │   │   │   ├── members.html
│   │   │   │   ├── post_page.html
│   │   │   │   └── settings.html
│   │   │   └── index.html
│   │   ├── layout.html
│   │   ├── messages
│   │   │   ├── conversation.html
│   │   │   └── index.html
│   │   ├── my_feed.html
│   │   ├── notifications.html
│   │   ├── notifications_unread.html
│   │   ├── post_page.html
│   │   ├── tags.html
│   │   └── users
│   │       ├── profile
│   │       │   ├── about.html
│   │       │   ├── friends.html
│   │       │   ├── groups.html
│   │       │   └── index.html
│   │       ├── profiles.html
│   │       ├── requests.html
│   │       └── settings.html
│   └── utils
│       ├── clear_all_db.py
│       ├── delete_db.py
│       ├── helpers.py
│       └── time_utils.py
├── requirements.txt
└── run.py
```

## User Instructions

### 1. Getting Started
1. Visit the deployed application at [Social50](https://cssocial50.com).
2. Register with your email and create a secure password.
3. Log in and complete your profile.

### 2. Exploring Features

1. Engage posts from other users on the feed.
2. Create posts to share ideas or ask questions.
3. Send friend requests and manage them.
4. Start messaging your friends.
5. Create or join groups.
6. Check the notifications dropdown for updates.

## How to Clone This Project

### Prerequisites

- Python 3.12
- Flask and related libraries (see `requirements.txt`)
- PostgreSQL (Alternatively you can use SQLite3)

### Steps

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/social-study-circle.git
   ```
2. Navigate to the project directory:
   ```bash
   cd social-study-circle
   ```
3. Create a virtual environment:
   ```bash
   python -m venv venv
   ```
4. Activate the virtual environment:
   - Windows:
     ```bash
     venv\Scripts\activate
     ```
   - Mac/Linux:
     ```bash
     source venv/bin/activate
     ```
5. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
6. Create and fill .env file with following variables:
   ```env
   FLASK_APP=run.py
   FLASK_ENV="development" or "production"
   SECRET_KEY=secret_key
   DATABASE_URL=your_database_url
   AWS_BUCKET_NAME=s3_bucket_name
   AWS_ACCESS_KEY=access_key
   AWS_SECRET_ACCESS_KEY=secret_access_key
   AWS_DOMAIN=aws_domain
   ```
7. Initialize the database migrations:
   ```bash
   flask db init
   flask db migrate -m "Initial migration"
   flask db upgrade
   ```
8. Run the application:
   ```bash
   flask run
   ```
9. Open `http://127.0.0.1:5000` in your browser.

## Acknowledgments

This project was developed as part of the final project for CS50's Introduction to Computer Science by Alican Avcuoğlu. You can find the resources I used in the [ACKNOWLEDGMENTS.md](ACKNOWLEDGMENTS.md)
