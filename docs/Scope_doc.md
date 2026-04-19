# Project Scope Document

**Document Metadata**

- **Creation Date:** April 18, 2026
- **Associated Design Doc:** Design Document - 15Apr2026
- **Group Members:** Ajay Paterson, Ashray Sikka, Michael Hubel
- **Course:** EXSM 3951 - Python Project

## 1. Project Title & Executive Summary

**Project Title:** Restaurant Franchise Reservation & Management System

**Executive Summary:**  
The Restaurant Franchise Reservation & Management System is a Python-based backend application designed to support a growing restaurant business with reservations, table management, online ordering (dine-in, take-out, and delivery), menu handling, loyalty programs, and basic inventory/stock management. 

The system will initially support a single restaurant location with the flexibility to scale to multiple locations in the future. It aims to streamline operations for restaurant staff and managers while providing customers with a convenient way to make reservations, place orders, and manage loyalty points. 

The ultimate business value is improved operational efficiency, better customer experience, and support for future expansion.

## 2. Project Objectives

### 2.1 Business Goals
- Enable efficient reservation and order management to maximize table utilization and reduce no-shows.
- Implement a loyalty program to encourage repeat business (10 points per dollar spent, redeemable for discounts).
- Support delivery within a 10 km radius with a distance-based fee structure.
- Provide managers with visibility into inventory levels to prevent stockouts.

### 2.2 Technical Goals
- Build a robust Python backend capable of handling reservations, orders, and inventory logic.
- Achieve reliable data persistence and basic validation for all core transactions.
- Ensure the system is modular and extensible to support future multi-location features.
- Maintain clean, well-documented code with appropriate unit tests for critical functions.

## 3. In-Scope

### 3.1 Core Features / Functionality
- Reservation system with table layout management (grid data seeded manually in v1; Table layout CSV upload deferred to Phase 2).
- Menu management (CSV upload) with allergen and dietary tagging.
- Online ordering for dine-in (pre-order), take-out, and delivery.
- Delivery fee calculation: $5 within 5 km, $10 within 10 km; flat $10 fallback if tiered calculation is too complex.
- Loyalty points system: 10 points per dollar spent (excluding tax), redeemable at 1000 pts = $10 off or 2000 pts = $25 off.
- Basic inventory management with min/max levels and low-stock alerts for managers only.
- User account management (customer accounts + guest checkout with deposit for reservations).
- Simple admin/manager panel for viewing reservations, orders, and inventory.
- Server/Host accounts with ability to update table status (occupied, empty, needs cleaning) from the floor.
- Delivery driver view showing assigned orders with customer contact info, delivery address, and order details.
- Cancellation policy: Free cancellation 3+ hours before reservation; $10 fee otherwise. Deposit required for all reservations (including guests).
- Kitchen dashboard with FIFO order queue and online order cutoff 30 minutes before closing time.
- Pseudo-payment processing: Visa and Mastercard only, always auto-approved.

### 3.2 API Endpoints
All key endpoints are defined in the associated **Software Design Document (SDD)**:
- Auth
- Reservations
- Orders
- Kitchen
- Inventory
- Loyalty
- Admin (CSV upload)
- Payments
- Delivery
- Tables

### 3.3 Data Models
The following models will be implemented:
- User
- Restaurant
- TableLayout
- Table
- Reservation
- MenuItem
- Order
- OrderItem
- Inventory
- LoyaltyTransaction
- Payment

### 3.4 Deliverables
- Fully functional v1.0 Python codebase on the `main` branch
- Entity Relationship Diagram (ERD)
- All wireframes
- Complete finalized Scope, Design, and Team Norms documents
- Test plan and test suite
- Fully complete, intuitive `README.md` with setup and usage instructions
- All GitHub Actions CI passing on `main`

## 4. Out-of-Scope

### 4.1 Excluded Features
- Advanced multi-location support (different menus, layouts, and independent operations per restaurant). The system is designed with future extensibility in mind (e.g., `location_id` / `restaurant_id` fields), but only a single location will be fully implemented in v1.
- Real-time kitchen display system or advanced order queuing visualizations.
- Complex reporting or analytics dashboards.
- Waitlist management or automated table-turn predictions.
- Support for high concurrent loads, horizontal scaling, or load balancing.
- Full data encryption at rest beyond SQLite defaults.
- Reservations larger than 20 people (special events handled via direct email to the restaurant).

### 4.2 Integrations
- No third-party payment gateways (pseudo-payment only).
- No external mapping/geolocation services for delivery distance (simplified tiered or flat-fee logic).
- No email/SMS notification services (notifications may be logged to console).
- No external loyalty or CRM systems.

### 4.3 Frontend / UI Work
- A functional HTML/CSS frontend using Django templates will be implemented.
- Mobile responsiveness and a fully polished UI are **not** in scope.
- No React or separate frontend framework.

### 4.4 Deferred to Phase 2
- Table layout CSV upload (only menu CSV uploads supported at launch).
- Live order status tracking.
- Delivery driver scope limited to read-only view of assigned orders in v1.

## 5. Target Audience & User Roles

### 5.1 Primary Users
- Customers (reservations, orders, loyalty points)
- Restaurant managers (inventory, alerts, oversight)
- Restaurant staff and delivery drivers (limited access)

### 5.2 User Roles & Permissions
- **Customer**: Register/login, make reservations, pre-order, view loyalty points, manage profile.
- **Guest**: Make reservations (with deposit), place takeout orders. No loyalty access.
- **Kitchen Staff**: View and update order statuses on kitchen dashboard only.
- **Delivery Driver**: View assigned delivery orders (customer info, address, order details). Read-only.
- **Manager**: Full access to inventory, low-stock alerts, all reservations and orders for their location, CSV uploads.
- **Owner**: Full access across all locations.
- **Server/Host**: View floor plan and update table status (occupied / empty / needs cleaning). No access to orders or customer data.

## 6. Assumptions & Dependencies

### 6.1 Technical Dependencies
- Python 3.11+
- Django
- Pytest + pytest-django
- SQLite (for development)
- GitHub Actions for CI

### 6.2 External Dependencies
- None required.
- Delivery fees use internal simplified logic (no Google Maps or GPS).
- Payments are fully simulated (pseudo-payment).

### 6.3 Infrastructure
- Local development machines with Git for version control.
- Optional simple hosting platform (e.g., Render free tier) for demonstration only.

## 7. Constraints

### 7.1 Time / Schedule
- Final launch/demo required by **May 25, 2026**.
- All MUST-HAVE features must be functional by this date.

### 7.2 Budget
- No financial budget. Development uses only free and open-source tools.

### 7.3 Technical Limitations
- No real-time payment gateway or live GPS tracking.
- Not designed for high concurrent load or horizontal scaling.
- Data not encrypted at rest beyond SQLite defaults.
- Maximum party size capped at 20.
- Table layout CSV upload not supported in v1.

### 7.4 Regulatory / Security
- No formal compliance requirements.
- Passwords hashed using Django’s PBKDF2 (never stored in plain text).
- No real payment data persisted.
- Strong input validation on all forms and CSV uploads.

## 8. Acceptance Criteria

### 8.1 Functional Completion
- Reservations can be created, viewed, and cancelled with correct fee logic.
- Menu displayed with allergen/dietary tags.
- Orders (dine-in/take-out/delivery) can be placed with correct fees.
- Loyalty points earned and redeemed correctly.
- Inventory levels managed with low-stock alerts for managers.
- Table status updates work for Server/Host role.
- Delivery driver can view assigned orders with full details.
- Guest accounts supported with deposit for reservations.
- Menu CSV upload works and items appear correctly.
- Single location fully functional with multi-location design extensibility.

### 8.2 Performance & Quality Metrics
- All Pytest unit and integration tests pass.
- GitHub Actions CI passes on the `main` branch.
- **80%+** test coverage on critical business logic.
- Core endpoints respond under 200ms in local testing.

### 8.3 Documentation
- Complete `README.md` with setup and usage instructions.
- Code comments and basic feature documentation.

### Launch Readiness
- System ready for demo on May 25, 2026 with all MUST-HAVE features working.
- All pull requests reviewed and merged to `main`.
- No failing tests on `main` at final submission.
- All "[TO BE MADE - WEEK 2]" placeholders replaced with actual files by Week 2.


