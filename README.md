# Hotel Management System — Gwalior Edition

A modern hotel booking website focused on **Gwalior, Madhya Pradesh**.  
Built with Flask + SQLite + Tailwind CSS (CDN) for a college engineering project expo.

## Features
- 9 unique hotels in Gwalior, each with exactly 6 distinct room types
- High-quality Unsplash images for hotels and rooms
- **Booked rooms are greyed out** (not hidden) with a red "Booked / Currently Occupied" badge
- Interactive booking modal → **Simulated Payment Portal** (UPI / Card / Net Banking)
- Itemized bill with **Indian Hospitality GST** (12% or 18%)
- **Staff Login** with hashed passwords (default: `admin` / `gwalior2026`)
- Staff dashboard with **Live KPI Cards** (Revenue, Active Check-ins, Available Rooms, Occupancy %)
- Customer **Track / Cancel Booking** page (`/my-booking`)
- Light / Dark mode toggle (saved in localStorage) — Ice Sky Blue / Abyssal Teal
- Custom themed 404 & 500 error pages
- Strict server-side validation and exception handling

## Project Structure
```
Hotel-Management-System/
├── app.py
├── requirements.txt
├── README.md
└── templates/
    ├── index.html
    ├── hotel_details.html
    ├── payment.html
    ├── my_booking.html
    ├── staff_login.html
    ├── staff.html
    └── error.html
```

## Setup & Run

1. Extract the zip.
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. **Important:** Delete `database.db` if it exists from a previous run so the new schema (payment fields + staff_users) loads correctly.
4. Run:
   ```bash
   python app.py
   ```
5. Open:
   - Customer site: http://127.0.0.1:5000
   - My Booking: http://127.0.0.1:5000/my-booking
   - Staff portal: http://127.0.0.1:5000/staff (login required)

**Staff Login:**  
Username: `admin`  
Password: `gwalior2026`  
(Login persists for 30 days after successful sign-in.)

## Notes
- All booking, guest-detail, pricing, and checkout logic is preserved and enhanced.
- Payment is fully simulated for demo purposes (no real gateway).
- Dark mode works across all pages including modals, payment, and staff dashboard.
- Suitable for school / college practical demonstration and project expo.
