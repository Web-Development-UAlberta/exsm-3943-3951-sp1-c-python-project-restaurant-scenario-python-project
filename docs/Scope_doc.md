# Project Scope Document

**Document Metadata**

- **Creation Date:** April 18, 2026
- **Associated Design Doc:** Design Document - 15Apr2026
- **Group Members:** Ajay Paterson, Ashray Sikka, Michael Hubel
- **Course:** EXSM 3951 Python Project

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
- User registration and login for customers, kitchen staff, managers, delivery drivers, and a franchise-level owner account.
- Guest accounts with reservation and takeout support (deposit required for reservations).
- Table reservation system with a 50x50 grid-based floor plan, date/time selection, and conflict prevention logic.
- Cancellation policy: Free cancellation 3+ hours before reservation, $10 fee otherwise. Deposit always required (including guest accounts).
- Menu browsing with images and allergen/dietary tags per dish.
- Pre-ordering for dine-in, takeout, and delivery (30-minute cutoff before needed time; cancel-only after commit).
- Delivery fee structure: $5 within 5km, $10 within 10km, no delivery beyond 10km.
- Pseudo-payment processing: Visa and Mastercard only, always auto-approved.
- Loyalty program: 10 points per dollar spent (excluding tax), 1000 pts = $10 off, 2000 pts = $25 off, no expiry, no partial redemption, max discount $25.
- Kitchen dashboard with FIFO order queue and status tracking (Received → Preparing → Ready → Delivered).
- Inventory management with min/max levels set by managers and low-stock alerts (visible to managers only).
- Server/Host ability to update table status (occupied, empty, needs cleaning) from the floor view.
- Delivery driver view showing assigned orders with customer contact info and order details.
- Branding: Trendy, back-to-Earth feel (color palette to be finalized by the team).

### 3.2 Frontend / UI Work
- Functional HTML/CSS frontend using Django templates for all core user flows.
- Mobile responsiveness and fully polished UI are **not** in scope.

### 3.3 Deliverables
- Fully functional version 1.0 Python codebase on the `main` branch.
- Entity Relationship Diagram (ERD).
- All wireframes.
- Complete finalized Scope, Design, and Team Norms documents.
- Test Plan.
- Fully complete, intuitive README with setup and usage instructions.
- All GitHub Actions CI passing on `main`.

## 4. Out-of-Scope

### 4.1 Excluded Features
- Real payment processing (no Stripe, PayPal, etc.).
- SMS or email notifications.
- Special event bookings beyond 20 people (handled via direct email).
- Seating preferences (restaurant is entirely non-smoking).
- Multi-language support.
- Mobile app.
- Delivery driver route tracking or third-party integration.
- Advanced multi-location support (only single location fully implemented, designed with future extensibility in mind).
- Real-time kitchen display system or complex visualizations.
- Complex reporting or analytics dashboards.
- Waitlist management or automated table-turn predictions.
- High concurrent load handling, horizontal scaling, or load balancing.

### 4.2 Integrations
- No third-party payment gateways.
- No external mapping / geolocation services (simplified tiered logic used).
- No email/SMS services.
- No external loyalty or CRM systems.

### 4.3 Deferred to Phase 2
- Table layout CSV upload.
- Live order status tracking.
- Advanced delivery driver features.

## 5. Target Audience & User Roles

### 5.1 ###
**Primary Users:**
- **Customers** – Make reservations, place orders, manage loyalty points.
- **Restaurant Managers** – Manage inventory, view alerts, oversee operations.
- **Restaurant Staff** – Kitchen staff, servers, hosts, delivery drivers.

## 6. Assumptions & Dependencies

- Built using a Python web framework with a relational database (details in Design Document).
- No external third-party services or APIs are required.
- Development on local machines with Git for version control.
- Deployment for demonstration purposes (local or simple hosting).

## 7. Constraints

- **Time/Schedule:** Final launch/demo required by **May 25, 2026**.
- **Budget:** No financial budget — only free and open-source tools.
- **Technical Limitations:**
  - No real-time payment or GPS tracking.
  - Not designed for high concurrent load.
  - Maximum party size capped at 20.
  - Table layout CSV upload not supported in v1.

 **Security:**
- Passwords hashed using Django’s PBKDF2.
- No real payment data stored.
- Strong input validation on all forms and CSV uploads.

## 8. Acceptance Criteria

### Functional Completion
- Reservations can be made, viewed, and cancelled (with correct fee logic).
- Menu displayed with images and allergen tags.
- Orders (dine-in/takeout/delivery) placed with appropriate fees.
- Loyalty points earned and redeemed correctly.
- Inventory levels managed with low-stock alerts.
- Table status updates work for server/host role.
- Delivery driver sees only assigned orders with full details.
- Guest accounts supported with deposit for reservations.
- Menu CSV upload functional.
- All core business rules enforced (cutoffs, fees, validations, role access).

### Performance & Quality Metrics
- All Pytest unit and integration tests pass.
- GitHub Actions CI passes on `main`.
- 100% test coverage on critical business logic.
- 80%+ on all 

### Documentation & Launch Readiness
- Complete README with setup and usage instructions.
- All documents finalized (no placeholders).
- System ready for launch on **May 25, 2026**.
- All pull requests reviewed and merged.

