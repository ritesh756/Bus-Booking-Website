# 🚌 Ritesh Tours & Travels — Bus Booking Website

A full-stack Bus Booking Web Application developed to simplify travel reservations for **Ritesh Tours and Travels**. The system allows users to search routes, select seats, book tickets, and manage their bookings in a user-friendly interface inspired by modern platforms like RedBus.

## 🌐 Live Demo

**🔗 [View Live Website](https://tours-hazel-phi.vercel.app)**

---

## ✨ Features

- **Search Buses** — Find buses by route and travel date
- **Seat Selection** — Visual seat map with real-time availability
- **Online Payment** — UPI QR code payment integration
- **Booking Management** — View, track, and cancel bookings
- **User Authentication** — Register, login, and profile management
- **Admin Panel** — Manage fleet, schedules, bookings, and users
- **Responsive Design** — Works on desktop, tablet, and mobile

## 🛠️ Tech Stack

| Layer | Technology |
|-------|------------|
| **Backend** | Python, Flask, SQLAlchemy |
| **Frontend** | HTML5, CSS3, JavaScript |
| **Database** | SQLite (Development) |
| **Deployment** | Vercel |
| **Icons** | Font Awesome 6.5 |
| **Fonts** | Google Fonts (Poppins) |

## 🚀 Quick Start

### Local Development

```bash
# Clone the repository
git clone https://github.com/ritesh756/Bus-Booking-Website.git
cd Bus-Booking-Website

# Install dependencies
pip install -r requirements.txt

# Run the application
python app.py
```

The app will start at `http://127.0.0.1:5000`

### Default Credentials

| Role | Email | Password |
|------|-------|----------|
| **Admin** | admin@riteshtravels.com | Ritesh |

## 📁 Project Structure

```
├── app.py                 # Main Flask application
├── models.py              # SQLAlchemy database models
├── requirements.txt       # Python dependencies
├── vercel.json            # Vercel deployment config
├── runtime.txt            # Python runtime version
├── static/
│   ├── css/style.css      # Stylesheet
│   └── js/main.js         # Client-side JavaScript
└── templates/
    ├── base.html          # Base layout
    ├── index.html         # Home page
    ├── search_results.html
    ├── seat_selection.html
    ├── payment.html
    ├── booking_confirmation.html
    ├── my_bookings.html
    ├── login.html
    ├── register.html
    ├── admin.html
    └── admin_login.html
```

## 🚌 Routes

| From | To | Distance | Duration |
|------|-----|----------|----------|
| Gadinglaj | Pune | ~340 km | ~7.5 hours |

## 💳 Payment

- **UPI** — Scan QR code to pay via any UPI app
- **Cash** — Pay at boarding point (Cash on Boarding)

## 📱 Contact

- **Phone:** +91 98765 43210
- **Email:** info@riteshtravels.com
- **Location:** Gadinglaj, Maharashtra

## 👨‍💻 Developer

**[@ritesh756](https://github.com/ritesh756)**

---

## 📄 License

© 2024 Ritesh Tours and Travels. All Rights Reserved.

---

> Built with ❤️ by [Ritesh](https://github.com/ritesh756) | Powered by [Vercel](https://vercel.com)
