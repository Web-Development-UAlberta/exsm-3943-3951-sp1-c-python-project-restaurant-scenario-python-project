# Project Scope Document

**Document Metadata**

- **Creation Date:** April 18, 2026
- **Associated Design Doc:** Design Document - 15Apr2026
- **Group Members:** Ajay Paterson, Ashray Sikka, Michael Hubel
- **Course:** EXSM 3951 Python Project

## 1. Project Title & Executive Summary

**Project Title:** Restaurant Franchise Reservation & Management System

**Executive Summary:**
The Restaurant Franchise Reservation & Management System is a Python-based backend application designed to support a growing restaurant business with reservations, table management, online ordering (dine-in, take-out, and delivery), menu handling, loyalty programs, and basic inventory/stock management. The system will initially support a single restaurant location with the flexibility to scale to multiple locations in the future. It aims to streamline operations for restaurant staff and managers while providing customers with a convenient way to make reservations, place orders, and manage loyalty points. The ultimate business value is improved operational efficiency, better customer experience, and support for future expansion.

## 2. Project Objectives

**Business Goals:**
- Enable efficient reservation and order management to maximize table utilization and reduce no-shows.
- Implement a loyalty program to encourage repeat business (10 points per dollar spent, redeemable for discounts).
- Support delivery within a 10 km radius with a distance-based fee structure.
- Provide managers with visibility into inventory levels to prevent stockouts.

**Technical Goals:**
- Build a robust Python backend capable of handling reservations, orders, and inventory logic.
- Achieve reliable data persistence and basic validation for all core transactions.
- Ensure the system is modular and extensible to support future multi-location features.
- Maintain clean, well-documented code with appropriate unit tests for critical functions.

## 3. In-Scope

**Core Features/Functionality:**
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

**API Endpoints:**
Full endpoint definitions are documented in the associated Design Document.

**Data Models:**
Full schema and data model definitions are documented in the associated Design Document.

**Deliverables:**
Listed are the planned deliverables to be shipped alongside the project:
- Functional complete version 1.0 Python codebase present on main branch
- The Entity Relationship Diagram (ERD)
- All wireframes
- Complete finalized Scope, Design, and Team Norms documents
- Test plan used
- Fully complete, intuitive README file that details setup and usage instructions
- All GitHub Actions CI passing on main

## 4. Out-of-Scope

**Excluded Features:**
- Real payment processing (no Stripe, PayPal, or actual card charging)
- SMS or email notifications to customers
- Special event bookings beyond 20 people (handled via direct email to restaurant)
- Seating preferences (no smoking/non-smoking distinction, entire restaurant is non-smoking)
- Multi-language support
- Mobile app
- Delivery driver route tracking or third-party delivery integration
- Advanced multi-location support (different menus, layouts, and independent operations per restaurant). The system will be designed with future multi-location extensibility in mind, but only a single location will be fully implemented.
- Real-time kitchen display system or order queuing visualizations beyond basic status updates
- Complex reporting or analytics dashboards (e.g., sales reports, peak hour analysis)
- Waitlist management or automated table-turn predictions
- System is not designed for high concurrent loads, horizontal scaling, or load balancing
- Maximum party size is hard capped at 20; special events handled via direct email to the restaurant

**Integrations:**
- No integration with third-party payment gateways (Visa/Mastercard will be simulated only; no real transactions).
- No integration with external mapping or geolocation services for precise delivery distance calculation. Delivery fees will use a simplified tiered or flat-fee logic.
- No integration with email/SMS notification services for reservations, order confirmations, or low-stock alerts (notifications may be logged or printed to console).
- No integration with external loyalty or CRM systems.

**Frontend/UI Work:**
- A functional HTML/CSS frontend will be implemented using Django templates for all core user flows.
- Mobile responsiveness and a fully polished UI are not in scope.

**Non-functional Boundaries:**
Listed are features not in scope for this project:
- Polished, complete UI design
- No map / GPS data for distance based fee logic

**Deferred to Phase 2:**
- Table layout CSV upload is out of scope for v1 due to complexity around existing reservations. Only menu CSV uploads are supported at launch.
- Live order status tracking is deferred to a future phase.
- Delivery driver scope is limited to read-only view of assigned orders in v1.

## 5. Target Audience & User Roles

**Primary Users:**
- Customers (making reservations, placing orders, managing loyalty points)
- Restaurant managers (viewing alerts, managing inventory, overseeing operations)
- Restaurant staff and delivery drivers (basic access)

**User Roles & Permissions:**
- **Customer:** Register/login, make reservations, pre-order meals, view loyalty points, manage profile.
- **Guest:** Make reservations (deposit required), place takeout orders. No loyalty program access.
- **Kitchen Staff:** View and update order statuses on kitchen dashboard only. No access to reservations or customer data.
- **Delivery Driver:** View assigned delivery orders including customer name, phone number, delivery address, and itemized order details. Read-only access, no other system access.
- **Manager:** Full access to inventory, low-stock alerts, all reservations and orders for their location, CSV uploads.
- **Owner:** Full access across all locations.
- **Server/Host:** View floor plan and update individual table status (occupied / empty / needs cleaning). No access to orders, reservations, or customer data.

## 6. Assumptions & Dependencies

**Technical Dependencies:**
The project uses a Python-based web framework with a relational database. The full technical stack is documented in the Design Document.

**External Dependencies:**
- No external third-party services or APIs are required for this project.

**Infrastructure:**
- Development on local machines with Git for version control.
- Deployment: Run locally or on a simple hosting platform for demonstration.

## 7. Constraints

**Time/Schedule:**
- Final launch/demo required by May 25, 2026.
- All MUST-HAVE features must be functional by this date.

**Budget:**
- No financial budget allocated, development uses free and open-source tools only.

**Technical Limitations:**
- No real-time payment gateway or live GPS tracking.
- The system is not designed for high concurrent load.
- No horizontal scaling or load balancing.
- Data is not encrypted at rest beyond database defaults.
- Maximum party size capped at 20; special events handled via direct email to the restaurant.
- Table layout CSV upload not supported in v1.

**Regulatory/Security:**
No formal compliance requirements are applicable to the project. The following security validations and methods will be in place:
- All passwords hashed using Django's default PBKDF2 algorithm, will never be stored in plain text
- No persistence on any real payment data
- Strong and secure input validation that is required for all forms and CSV uploads

## 8. Acceptance Criteria

**Functional Completion:**
- Reservations can be made, viewed, and cancelled (with 3-hour rule noted).
- Menu displayed with allergen tags.
- Orders (dine-in/take-out/delivery) can be placed with appropriate fees.
- Loyalty points earned and redeemed correctly.
- Inventory levels can be set and low-stock alerts generated for managers.
- The system supports single location with future multi-location extensibility in design.
- Table status updates by server/host role function correctly.
- Delivery driver view shows assigned orders with correct customer contact info and order details.
- Guest accounts can make reservations with deposit and place takeout orders.
- Cancellation fee of $10 applies correctly when cancellation is within 3 hours of reservation time.
- Admin can upload menu CSV and verify items appear in the system.

**Performance Metrics:**
- All Pytest unit and integration tests pass.
- GitHub Actions CI passes on the main branch at time of submission.
- 80%+ test coverage on all critical business logic.

**Documentation:**
- README with setup and usage instructions.
- Comments in code and basic feature documentation.

**Launch Readiness:**
- The system is ready for launch on May 25, 2026, with all MUST-HAVE features working as specified.
- All pull requests reviewed and merged to main with required approvals.
- No failing tests on the main branch at time of final submission.
- All "File [TO BE MADE - WEEK 2]" placeholders in documentation will be replaced with actual files by Week 2.