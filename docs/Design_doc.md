# Software Design Document (SDD)

**Project Name:** Restaurant Franchise Reservation & Management System  
**Submitted by:** Ashray Sikka, Ajay Paterson, Michael Hubel  
**Date:** Apr 18, 2026  
**Course:** EXSM 3951 - Python Project


## 1. Introduction

### 1.1 Purpose

This system is being built for a restaurant franchise owner who currently has no digital way to handle reservations, ordering, or kitchen operations. Right now everything is presumably handled manually: phone calls, walk-ins, paper-based inventory. This platform gives customers a self-serve way to book tables and pre-order meals online, while giving restaurant staff the tools to manage orders, track inventory, and run kitchen operations without manual overhead. The end goal is a system that works for one location today and can scale to multiple locations as the franchise grows.

### 1.2 Scope

**In-Scope:**
- User registration and login for customers, kitchen staff, managers, delivery drivers, and a franchise-level owner account
- Guest accounts with reservation and takeout support (deposit required for reservations)
- Table reservation system with a 50x50 grid-based floor plan, date/time selection, and conflict prevention logic
- Cancellation policy: free cancellation 3+ hours before reservation, $10 fee otherwise. A deposit is always required for reservations including guest accounts
- Menu browsing with allergen/dietary tags per dish
- Pre-ordering for dine-in, takeout, and delivery (cutoff: 30 minutes before order needed, cancel-only after commit)
- Delivery fee structure: $5 within 5km, $10 within 10km, no delivery beyond 10km. Flat $10 fallback if distance calculation is too complex
- Pseudo-payment processing: Visa and Mastercard only, always auto-approved
- Loyalty program: 10 points per dollar spent (excluding tax), 1000 points = $10 off, 2000 points = $25 off, no expiry, no partial redemption, max discount $25
- Kitchen dashboard with FIFO order queue, order status tracking (Received, Preparing, Ready, Delivered), and online order cutoff 30 minutes before closing time
- Inventory management with per-ingredient min/max levels set by managers, low-stock alerts sent to managers only
- Branding: trendy, back-to-Earth feel. Color palette to be decided by the team
- Server/Host accounts with ability to update table status (occupied, empty, needs cleaning) from the floor
- Delivery driver view showing assigned orders with customer contact info, delivery address, and order details to prevent mix-ups on multi-order runs

**Out-of-Scope:**
- Real payment processing (no Stripe, PayPal, or actual card charging)
- SMS or email notifications to customers
- Special event bookings beyond 20 people (handled via direct email to restaurant)
- Seating preferences (no smoking/non-smoking distinction, entire restaurant is non-smoking)
- Multi-language support
- Mobile app
- Delivery driver route tracking or third-party delivery integration

**Limitations (Deferred to Phase 2):**
- Table layout CSV upload is out of scope for v1 due to complexity around existing reservations. Only menu CSV uploads will be supported at launch.
- Live order status tracking is deferred to a future phase.

### 1.3 Definitions

| Term | Definition |
|---|---|
| SDD | Software Design Document. This file. |
| ORM | Object-Relational Mapper. Maps Python classes to database tables so we write Python instead of raw SQL. We are using Django's built-in ORM. |
| API | Application Programming Interface. The set of URL endpoints our backend exposes for the frontend to talk to. |
| RBAC | Role-Based Access Control. Different users get different permissions based on their role (customer, manager, kitchen staff, etc.) |
| ERD | Entity-Relationship Diagram. A visual map of our database tables and how they relate to each other. |
| CSV | Comma-Separated Values. The file format the admin uploads to load the menu into the system. |
| Grid | The 50x50 coordinate system representing a restaurant's floor plan. Each cell is 1x1. A 4-person table takes 1 cell, larger tables span multiple cells. |
| Pseudo-Payment | A simulated checkout flow that always returns an approved status. No real money moves. |
| FIFO | First In, First Out. Kitchen processes orders in the order they were received, no priority by order type. |
| CI | Continuous Integration. GitHub Actions automatically runs our test suite on every push to main and every pull request. |


## 2. System Architecture

### 2.1 High-Level Architecture

The system uses a standard three-tier architecture:

- **Frontend (Presentation Layer):** HTML and CSS pages rendered by Django templates. Minimal JavaScript for dynamic interactions like grid rendering.
- **Backend (Application Layer):** Django handles routing, business logic, authentication, and all interactions with the database.
- **Database (Data Layer):** SQLite for development. All data lives here, users, reservations, orders, inventory, menus, and table configurations.

The frontend never talks to the database directly. Everything goes through Django views and the ORM. This is a monolithic architecture, one codebase, one server, everything bundled together. Simple, appropriate for this project scope.

Diagram Reference: File [TO BE MADE - WEEK 2]

### 2.2 Technology Stack

| Component | Technology |
|---|---|
| Backend Framework | Django (Python) |
| Language/Runtime | Python 3.11+ |
| Database | SQLite |
| Frontend | HTML, CSS, JavaScript |
| Testing | Pytest + pytest-django |
| CI | GitHub Actions (runs tests on every push to main and every PR) |
| Version Control | Git via GitHub Classroom |
| Deployment/Containerization | Not in scope for this project |


## 3. Detailed Design

### 3.1 Database Schema/Data Models

- **User:** id, first_name, last_name, email, password_hash, phone_number, address, role (customer / kitchen_staff / delivery_driver / server / manager / owner), loyalty_points, is_guest, created_at
- **Restaurant:** id, name, address, city, phone, email, opening_time, closing_time
- **TableLayout:** id, restaurant_id (FK → Restaurant), grid_data (JSON representing the 50x50 matrix), uploaded_at — model defined for v1; CSV upload mechanism deferred to Phase 2
- **Table:** id, restaurant_id (FK → Restaurant), label, seats, grid_squares (JSON list of x/y coordinates the table occupies), status (occupied / empty / needs_cleaning / reserved)
- **Reservation:** id, user_id (FK → User, nullable for guests), guest_name, guest_email, guest_phone, table_id (FK → Table), restaurant_id (FK → Restaurant), reserved_at (datetime), party_size, status (confirmed / cancelled), deposit_amount, cancellation_fee_applied, created_at
- **MenuItem:** id, restaurant_id (FK → Restaurant), name, description, price, category, is_available, tags (JSON list, e.g. ["vegan", "contains nuts"])
- **Order:** id, user_id (FK → User, nullable for guests), restaurant_id (FK → Restaurant), reservation_id (FK → Reservation, nullable), order_type (dine-in / takeout / delivery), assigned_driver_id (FK → User, nullable, delivery orders only), delivery_address, delivery_fee, subtotal, loyalty_discount, total_price, payment_status, order_status (received / preparing / ready / delivered), created_at
- **OrderItem:** id, order_id (FK → Order), menu_item_id (FK → MenuItem), quantity, unit_price, special_instructions
- **Inventory:** id, restaurant_id (FK → Restaurant), ingredient_name, quantity, unit, min_level, max_level, is_low_stock
- **LoyaltyTransaction:** id, user_id (FK → User), order_id (FK → Order), points_earned, points_redeemed, created_at
- **Payment:** id, order_id (FK → Order), method (visa / mastercard), amount, status (always "approved" for this project), processed_at

Full Schema Reference: File [TO BE MADE - WEEK 2]

### 3.2 API Endpoints

Since we are using Django with server-rendered templates, most interactions happen through Django views rather than a pure REST API. Below are the key URL routes:

**Auth**
- `POST /auth/register/` — Create a new customer account
- `POST /auth/login/` — Log in and create a session
- `POST /auth/logout/` — End the session
- `POST /auth/guest/` — Start a guest session

**Restaurants**
- `GET /restaurants/` — List all locations
- `GET /restaurants/<id>/` — View a specific location
- `GET /restaurants/<id>/layout/` — View the 50x50 grid for a location (grid data seeded manually in v1; CSV upload deferred to Phase 2)
- `GET /restaurants/<id>/menu/` — View the menu for a location

**Reservations**
- `GET /reservations/available/` — Check available tables for a date/time/location
- `POST /reservations/create/` — Create a reservation
- `POST /reservations/<id>/cancel/` — Cancel a reservation (applies fee logic)

**Orders**
- `POST /orders/create/` — Submit a new order
- `GET /orders/<id>/` — View order details
- `POST /orders/<id>/cancel/` — Cancel an order (only if 30+ min before needed)

**Kitchen**
- `GET /kitchen/orders/` — Kitchen dashboard with FIFO order queue
- `POST /kitchen/orders/<id>/status/` — Update order status

**Delivery**
- `GET /delivery/orders/` — View all orders assigned to the logged-in driver
- `GET /delivery/orders/<id>/` — View full details for a specific assigned order

**Tables**
- `POST /tables/<id>/status/` — Update table status (server/host role only — occupied / empty / needs_cleaning / reserved)

**Inventory**
- `GET /inventory/` — View all inventory items (manager only)
- `POST /inventory/<id>/update/` — Update quantity or min/max levels

**Loyalty**
- `GET /loyalty/<user_id>/` — View points balance and transaction history

**Admin**
- `POST /admin/upload/menu/` — Upload CSV for menu items

**Payments**
- `POST /payments/process/` — Process pseudo-payment (always approved)


## 4. User Interface Design

### 4.1 Wireframes/Views

**Public / Guest**
- **Home / Landing Page:** Franchise intro, location selector, call-to-action to reserve or order
- **Location Detail Page:** Restaurant info, hours, link to menu and reservation flow

**Reservation Flow**
- **Step 1:** Date, time, party size, and location selector
- **Step 2:** 50x50 grid floor plan with available tables highlighted, click to select
- **Step 3:** Reservation summary with deposit and cancellation policy displayed
- **Step 4:** Guest info or login prompt, then confirmation

**Menu & Ordering**
- **Menu Page:** Items grouped by category, allergen/dietary tags visible on each item, add to order button
- **Order Summary:** Cart view with order type selector (dine-in/takeout/delivery), delivery address field if delivery, loyalty redemption option, total with fee breakdown
- **Checkout:** Visa/Mastercard input fields, submit button, confirmation screen

**Customer Dashboard (logged-in only)**
- Active reservations and orders
- Loyalty points balance and transaction history
- Profile and address management

**Kitchen Dashboard (kitchen staff only)**
- Live FIFO order queue with timestamps
- Status update buttons: Received → Preparing → Ready → Delivered
- Visual indicator for orders approaching time

**Delivery Driver View (delivery driver role only)**
- List of orders assigned to the driver for their current shift
- Per order: customer name, phone number, delivery address, and itemized order details
- Visual separation between multiple active orders to prevent mix-ups

**Server / Host View (server role only)**
- Floor view showing table statuses on the grid
- Ability to update individual table status: Empty → Occupied → Needs Cleaning → Empty

**Manager / Admin Panel**
- CSV upload forms for menu
- Inventory table with current levels, min/max settings, low-stock flags
- All reservations and orders for their location
- Low-stock alert list

Wireframe Document: File [TO BE MADE - WEEK 2]

### 4.2 Navigation Structure

- **Public/Guest:** Home → Select Location → Reserve Table → Menu → Checkout → Confirmation
- **Logged-in Customer:** Above + Dashboard → Order History → Loyalty → Profile
- **Kitchen Staff:** Kitchen Dashboard only (isolated, no access to anything else)
- **Delivery Driver:** Assigned Orders → Order Detail View
- **Manager:** Manager Panel → Inventory → Upload CSV → All Orders → All Reservations
- **Owner:** Full access across all locations
- **Server/Host:** Floor View → Table Status Update


## 5. Security Considerations

### 5.1 Authentication and Authorization

- **Authentication:** Django's built-in session-based authentication. Users log in with email and password. Sessions are managed server-side via Django's session framework.
- **Authorization:** RBAC with six roles — Customer, Kitchen Staff, Delivery Driver, Server/Host, Manager, Owner. Django's permission system and custom decorators will restrict access to views based on role. For example, the kitchen dashboard is only accessible to kitchen_staff and manager roles, and the delivery view is only accessible to delivery_driver and manager roles.

### 5.2 Data Protection

- Passwords are hashed using Django's default PBKDF2 algorithm. Never stored in plain text.
- No real payment data is persisted beyond the transaction record (method type and auto-approved status only).
- Input validation on all forms and CSV uploads to prevent malformed data from entering the database.
- Guest accounts store minimal PII (name, email, phone) only as required to complete the reservation or order.
- Delivery addresses are stored only on orders where order_type is 'delivery'.


## 6. Testing Strategy

### 6.1 Unit Testing

**Tool:** Pytest with pytest-django  
**Coverage Goal:** 80%+ on all critical business logic

Priority areas to test:
- Reservation conflict detection (is the table actually free in the time window?)
- Cancellation fee logic (is it within 3 hours or not?)
- Delivery fee calculation (5km = $5, 10km = $10, beyond = rejected)
- Loyalty points calculation (10 points per dollar, correct redemption tiers)
- Pre-order cutoff enforcement (30-minute rule)
- Kitchen order cutoff (30 minutes before closing)
- CSV parsing for menu uploads
- Grid logic for multi-square table placement
- Table status transitions (server updating occupied / empty / needs_cleaning and verifying correct role enforcement)
- Delivery driver order assignment (driver only sees their own assigned orders, not other drivers' orders)

### 6.2 Integration Testing

API endpoints and Django views will be tested against a dedicated test database (SQLite, separate from dev). Each key view will be hit with valid and invalid inputs to verify correct HTTP responses, redirects, and database state changes. Django's built-in test client will be used for this.

### 6.3 End-to-End Testing

Full user workflows will be manually verified and where possible covered by pytest-django test cases simulating complete flows:
- Full reservation booking from location selection to confirmation
- Pre-order with loyalty redemption and checkout
- Kitchen staff receiving and updating an order through all statuses
- Manager uploading a CSV and verifying menu appears correctly
- Cancellation with and without the fee being applied
- Server/Host updating table status through a full cycle and verifying it reflects correctly on the floor view
- Delivery driver logging in and viewing assigned orders with correct customer contact info, address, and order details across multiple simultaneous orders


## 7. Deployment Plan

### 7.1 Development Environment

Each developer runs the project locally using a Python virtual environment. SQLite is the default dev database, no external database setup needed. Setup instructions will be in docs/README.md covering virtual env creation, dependency installation via requirements.txt, running migrations, and starting the dev server.

### 7.2 Staging Environment

GitHub Actions runs the full Pytest suite automatically on every push to main and every pull request. No merge happens without passing tests and 1 PR approval. This is our CI gate and acts as a lightweight staging check.

### 7.3 Production Environment

Not formally in scope. If we deploy to a live URL for demo purposes, we will use Render or a similar free-tier host. SQLite carries over for simplicity at this stage since we are not expecting real traffic.


## 8. Timeline and Milestones

| Phase | Description | Duration | Target Completion |
|---|---|---|---|
| Phase 1: Planning | Team norms, scope draft, design draft, GitHub repo setup and branch protection | Week 01 | Apr 19, 2026 11:45 PM MST |
| Phase 2: Design Finalization | Final ERD, final wireframes, final test plan, scope issues entered in GitHub Issues | Week 02 | Apr 26, 2026 11:45 PM MST |
| Phase 3: Core Backend | Django project setup, ORM models, migrations, auth system, reservation logic, back-end tests in CI | Week 03 | May 3, 2026 11:45 PM MST |
| Phase 4: Business Logic | Orders, kitchen dashboard, inventory, loyalty, delivery fee logic, front-end tests, README setup section | Week 04 | May 10, 2026 11:45 PM MST |
| Phase 5: Release Candidate | All features implemented, README usage section complete, all tests passing on main | Week 05 | May 17, 2026 11:45 PM MST |
| Phase 6: Final Presentation | Live demo, Q&A with instructor as client, post-presentation revisions | Week 06 | May 24, 2026 11:45 PM MST |


## 9. Appendix

### 9.1 References

- Project Specification: EXSM 3951 Project Specification PDF
- Client Q&A Document: Client_Answers_17Apr2026.pdf
- Django Documentation: https://docs.djangoproject.com
- Pytest + pytest-django: https://pytest-django.readthedocs.io
- GitHub Actions Documentation: https://docs.github.com/en/actions
- Draw.io for ERD and wireframes: https://app.diagrams.net
- Django ORM Reference: https://docs.djangoproject.com/en/stable/topics/db/models/