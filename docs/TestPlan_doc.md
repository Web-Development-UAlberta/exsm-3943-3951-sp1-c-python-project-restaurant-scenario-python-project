# Test Plan - Restaurant Management System

**Version:** 1.1   
**Date:** April 25, 2026  
**Prepared by:** Michael Hubel  
**Project:** Restaurant Management System

## 1. Introduction

### 1.1 Purpose
This Test Plan describes the overall testing strategy, scope, approach, resources, and schedule for the Restaurant Management System. It ensures the system functions correctly according to the requirements in the Scope Document, with strong emphasis on input validation, business rules, and edge-case handling.

### 1.2 Project Overview
The Restaurant Management System is a web application that allows customers to make reservations, browse the menu, and place orders for dine-in, takeout, or delivery. Staff members (servers, kitchen staff, managers, delivery drivers, and owners) can manage tables, reservations, orders, and basic operations. The system also includes loyalty points tracking.

### 1.3 Testing Objectives

* Verify all in-scope features work as expected
* Ensure proper role-based access control for different user types
* Validate critical end-to-end flows (reservation, ordering, payment)
* Check data consistency (orders, table status, loyalty points)
* Strong focus on input validation, boundary values, and "what is allowed vs. not allowed"
* Identify defects early in development

## 2. Scope of Testing

### 2.1 In-Scope

* User registration, login, logout, and role-based access (customer, server, kitchen_staff, delivery_driver, manager, owner, guest)
* Restaurant basic setup (information, tables, menu items)
* Reservations (create, view, status updates: confirmed → seated → completed/cancelled)
* Ordering flows (dine-in with table, takeout, delivery with address)
* Order management and status updates
* Menu browsing and item selection
* Basic payment processing
* Loyalty points earning and redeeming
* Input validation and basic error handling

### 2.2 Out-of-Scope

* Full inventory management with recipe linking
* Advanced analytics and reporting. Basic reporting is included (menu item sales, ingredient usage summaries, etc); complex dashboards, trend forecasting and data exports are out of scope.
* Real external payment gateway or delivery service integration
* Performance and load testing
* Mobile application testing (web only)
* CSV based floor plan uploads. Table layout is managed through the built-in visual grid interface only.

## 3. Testing Approach

### 3.1 Types of Testing

* Unit Testing (individual functions and calculations)
* Integration Testing (e.g., Order + OrderItem + Payment + Loyalty)
* Functional and System Testing (end-to-end user scenarios)
* User Interface and Usability Testing
* Manual Exploratory Testing
* Regression Testing after changes
* Basic Security Testing (authentication, input validation, authorization)

### 3.2 Testing Method

* Automated testing using Pytest and pytest-django is the primary approach for all critical business logic.
* Manual testing covers UI flows, usability and exploratory scenarios
* Github Actions runs the full test suite automatically on every push to main and every pull request

### 3.3 Automated Testing Considerations
We plan to automate key validation rules and business logic so regressions are caught quickly:

* Address validation: Delivery orders must have a valid address. No address → blocked.
* Loyalty points redemption: Cannot redeem more value than the order total (no negative totals). Points have no cash value beyond discount.
* Price / numeric field validation: Prices cannot be negative, zero (for paid items), or non-numeric.
* Reservation conflict detection: table cannot be booked if occupied within the next hour (rounded up to half hour)
* Cancellation fee logic: free if 3+ hours before, $10 fee if within 3 hours
* Delivery fee calculation: 5km = $5, 10km = $10, beyond = rejected
* Pre-order cutoff: orders must be placed 30+ minutes before needed
* Kitchen order cutoff: no orders accepted 30 minutes before closing
* Loyalty points tiers: 1000 pts = $10, 2000 pts = $25, max $25 discount, no partial redemption
* Role enforcement: each protected view must reject unauthorized roles
* Grid logic: multi-square table placement must not overlap
* Table status transitions: only valid status changes allowed
* Other rules: Quantity must be positive integer, menu item must exist and be available, etc.

These can be implemented as unit tests on models/forms and integration tests on views.

## 4. Test Environment

* Local development environment (Django + SQLite)
* Docker-based setup (if applicable)
* Browsers: Chrome and Firefox (latest versions)
* Test Data: Sample users with different roles, restaurants, menus, tables, and orders
* pytest-django test database (separate SQLite instance, auto-created and torn down per test run).

## 5. Test Schedule

* Test Plan Draft: April 21–25, 2026
* Detailed Test Case Development: A detailed and organized testing schedule will be discussed and created following weekly requirements and tasks. Steps will be taken to ensure adequate time is allotted for proper testing and iteration.
* Initial Test Execution: Initial test execution will be commenced as features are complete and working.
* Bug Fixing and Retesting: A phase commenced after features are complete and working. Comprises adding / iterating upon feedback given while also fixing any bugs or unwanted functionality and once fixed, retesting to ensure optimal, responsive, clean performance.
* Final Test Report: Before May 25th, 2026 in time for the “release candidate”

## 6. Roles and Responsibilities
We are aiming for 100% coverage on all critical business logic functions with +80% coverage on the overall codebase. 

All critical logic includes:

* Reservation
* Conflict detection
* Cancellation fee
* Delivery fee calculation
* Loyalty points math
* Order cutoff enforcement
* Role-based access checks

- Test Coordinator: Michael
- Testers: All group members
- Developers: Fix reported issues
- Reviewer: Whole group

## 7. Risks and Mitigation

* Risk: Changing requirements  
  Mitigation: Cross-check with Scope Document and ERD regularly

* Risk: Lack of realistic test data  
  Mitigation: Prepare seed data early

* Risk: Time constraints  
  Mitigation: Prioritize critical paths (login → reservation → order → payment)

* Risk: Role-based permission issues  
  Mitigation: Test each feature with multiple roles

## 8. Entry and Exit Criteria

* Entry Criteria: Scope Document finalized, ERD Revision 1 complete, core features under development
* Exit Criteria: All high-priority test cases passed, major defects resolved or documented

## 9. Sample Test Cases
Test cases are grouped by functional area for better readability and traceability.

### 9.1 User Management & Authentication

| Test ID | Scenario                    | Test Description                              | Expected Result                        | Failure Conditions                     | Test Type   | Priority |
|---------|-----------------------------|-----------------------------------------------|----------------------------------------|----------------------------------------|-------------|----------|
| TC-01   | User Registration           | Attempt registration with valid + invalid data | Account created with correct role      | Duplicate email, invalid format, missing fields | Integration | High     |
| TC-60   | Duplicate Email             | Register with existing email                  | Registration blocked with clear error  | Duplicate account created              | Integration | High     |
| TC-61   | Missing Required Fields     | Submit form with missing name/phone/address   | Field-specific errors shown            | Incomplete account created             | Integration | High     |
| TC-62   | Wrong Password              | Login with incorrect password                 | Login rejected                         | Login succeeds                         | Integration | High     |
| TC-02   | Role-based Login & Access   | Login as each role and test restricted actions| Only permitted features visible        | Unauthorized access allowed            | Manual      | High     |
| TC-10   | Guest Checkout              | Place order as guest (no login)               | Order succeeds                         | Critical fields missing                | Integration | High     |

### 9.2 Reservations

| Test ID | Scenario                        | Test Description                              | Expected Result                        | Failure Conditions                     | Test Type   | Priority |
|---------|---------------------------------|-----------------------------------------------|----------------------------------------|----------------------------------------|-------------|----------|
| TC-03   | Create Reservation              | Valid/invalid times, overlapping, party size  | Reservation created + table updated    | Overlapping, past time, invalid size   | Integration | High     |
| TC-17   | Reservation Conflict Detection  | Book already reserved table (next hour)       | Booking rejected                       | Double booking allowed                 | Unit        | High     |
| TC-37   | Party Size Limit                | Book for 21+ people                           | Rejected with contact message          | Booking accepted                       | Unit        | High     |
| TC-38   | Past Date/Time                  | Book in the past                              | Rejected                               | Past booking accepted                  | Unit        | High     |
| TC-39   | Outside Operating Hours         | Book outside open hours                       | Rejected                               | Booking accepted                       | Unit        | High     |
| TC-40   | Deposit Amount                  | Complete reservation                          | $10 deposit charged                    | Wrong or no deposit                    | Unit        | High     |
| TC-18   | Cancellation – Free Window      | Cancel 3+ hours before                        | No fee                                 | Fee incorrectly applied                | Unit        | High     |
| TC-19   | Cancellation – Within 3 Hours   | Cancel <3 hours before                        | $10 fee applied                        | Fee not applied                        | Unit        | High     |
| TC-31   | Guest Reservation Deposit       | Guest books without deposit                   | Blocked until deposit                  | Accepted without deposit               | Integration | High     |

### 9.3 Ordering & Payment

| Test ID | Scenario                          | Test Description                          | Expected Result                        | Failure Conditions                     | Test Type   | Priority |
|---------|-----------------------------------|-------------------------------------------|----------------------------------------|----------------------------------------|-------------|----------|
| TC-05   | Dine-in Order Creation            | Add items to table, send to kitchen       | Order created & sent                   | No items or invalid item               | Integration | High     |
| TC-41   | Cancel After Commit               | Edit order after submission               | Edit blocked                           | Order still editable                   | Integration | High     |
| TC-42   | Empty Cart Checkout               | Submit order with 0 items                 | Blocked with error                     | Empty order submitted                  | Integration | High     |
| TC-11   | Order Total & Payment Calculation | Add items + discount/points               | Correct total, tax, final amount       | Negative totals or wrong rounding      | Unit        | High     |
| TC-45   | Payment – Visa/Mastercard Only    | Use unsupported card                      | Blocked                                | Unsupported method accepted            | Unit        | High     |
| TC-46   | Payment – Auto Approval           | Valid Visa/Mastercard                     | Always approved                        | Payment rejected                       | Integration | High     |

### 9.4 Delivery Specific

| Test ID | Scenario                            | Test Description                        | Expected Result                        | Failure Conditions                     | Test Type   | Priority |
|---------|-------------------------------------|-----------------------------------------|----------------------------------------|----------------------------------------|-------------|----------|
| TC-06   | Delivery – Address Validation       | Create delivery with/without address    | Succeeds only with valid address       | No address → blocked                   | Unit        | High     |
| TC-20   | Delivery Fee – 5km                  | Address ≤5km                            | Fee = $5                               | Wrong fee                              | Unit        | High     |
| TC-21   | Delivery Fee – 10km                 | 5–10km                                  | Fee = $10                              | Wrong fee                              | Unit        | High     |
| TC-22   | Delivery Fee – >10km                | Beyond 10km                             | Rejected, suggest takeout              | Delivery allowed                       | Unit        | High     |
| TC-50   | Delivery – Geocoding Fallback       | Simulate geocoding failure              | Fallback zone dropdown appears         | Checkout completely blocked            | Integration | High     |
| TC-51   | Delivery Driver – Own Orders Only   | Driver views orders                     | Only own assignments visible           | Sees all orders                        | Manual      | High     |
| TC-52   | Delivery – Order Details Accuracy   | Driver view                             | All details match record               | Missing/incorrect info                 | Manual      | High     |

### 9.5 Loyalty Points

| Test ID | Scenario                    | Test Description                    | Expected Result                  | Failure Conditions       | Test Type | Priority |
|---------|-----------------------------|-------------------------------------|----------------------------------|--------------------------|-----------|----------|
| TC-07   | Over-Redemption             | Redeem $20 on $10 order             | Prevented or capped              | Negative total allowed   | Unit      | High     |
| TC-25   | Correct Tier Redemption     | Redeem 1000 pts on $15 order        | $10 discount                     | Wrong discount           | Unit      | High     |
| TC-26   | Partial Redemption Blocked  | Redeem 500 pts                      | Blocked                          | Partial allowed          | Unit      | High     |
| TC-27   | Max Discount Cap            | Redeem 2000 pts on $30 order        | $25 max discount                 | Exceeds $25              | Unit      | High     |
| TC-15   | Loyalty Points Earning      | Complete order                      | Points added correctly           | Not awarded / wrong amount | Unit    | High     |
| TC-36   | Earning Calculation         | $50 order                           | 500 points (subtotal only)       | Wrong calculation        | Unit      | High     |
| TC-47   | Guest Account               | Order as guest                      | No points awarded                | Points awarded           | Unit      | High     |
| TC-48   | Tax Exclusion               | $50 + $5 tax                        | Points on $50 only               | On full total            | Unit      | Medium   |
| TC-49   | No Expiry                   | Points after inactivity             | Balance unchanged                | Expire/reset             | Unit      | Medium   |

### 9.6 Menu, Inventory & Kitchen

| Test ID     | Scenario                          | Test Description                        | Expected Result                        | Failure Conditions                     | Test Type   | Priority |
|-------------|-----------------------------------|-----------------------------------------|----------------------------------------|----------------------------------------|-------------|----------|
| TC-08       | Menu Item Price Validation        | Negative, zero, non-numeric price       | Only positive numeric accepted         | Invalid prices saved                   | Unit        | High     |
| TC-09       | Quantity Validation               | 0, negative, decimal, huge qty          | Only positive integers                 | Invalid quantities accepted            | Unit        | High     |
| TC-12       | Menu Item Availability            | Out-of-stock item                       | Cannot be added                        | Can be ordered                         | Integration | Medium   |
| TC-43       | Unavailable Menu Item             | Add unavailable item                    | Blocked                                | Added to order                         | Integration | High     |
| TC-53       | Kitchen FIFO Order                | Place 3 orders                          | Oldest first                           | Wrong sequence                         | Integration | High     |
| TC-54       | Kitchen Status Progression        | Received → Preparing → Ready            | Each update saved                      | Skips incorrectly                      | Integration | High     |
| TC-57       | Non-Manager Inventory Access      | Kitchen/server tries to access          | Access denied                          | Can access                             | Manual      | High     |

### 9.7 Role-Based Access & Security

| Test ID | Scenario                    | Test Description                        | Expected Result               | Failure Conditions         | Test Type | Priority |
|---------|-----------------------------|-----------------------------------------|-------------------------------|----------------------------|-----------|----------|
| TC-28   | Kitchen Staff Access        | Try reservations page                   | Access denied                 | Can view                   | Manual    | High     |
| TC-29   | Delivery Driver Access      | View other driver’s orders              | Denied                        | Can see others             | Manual    | High     |
| TC-30   | Server/Host Access          | Try inventory/management                | Denied                        | Can access                 | Manual    | High     |
| TC-63   | Owner Cross-Location        | Owner login                             | Sees all locations            | Restricted                 | Manual    | High     |
| TC-16   | Location Toggle (Inactive)  | Deactivate restaurant                   | Customers blocked from actions| Still usable               | Integration | Medium |

### 9.8 Table & Status Management

| Test ID | Scenario                    | Test Description                        | Expected Result               | Failure Conditions         | Test Type   | Priority |
|---------|-----------------------------|-----------------------------------------|-------------------------------|----------------------------|-------------|----------|
| TC-04   | Table Status Management     | Normal flow + direct manipulation       | Consistent updates            | Invalid transitions        | Integration | High     |
| TC-32   | Valid Status Transition     | Empty → Occupied                        | Updates correctly             | Invalid accepted           | Integration | High     |
| TC-33   | Invalid Status Transition   | Undefined status                        | Rejected                      | Saved to DB                | Unit        | High     |
| TC-58   | Server POS Order            | Place dine-in via floor view            | Correctly linked & sent       | Not linked/sent            | Integration | High     |
| TC-59   | Server Bill Generation      | Generate bill for table                 | Correct data                  | Incorrect or fails         | Manual      | High     |

### 9.9 Error Handling & Usability

| Test ID     | Scenario                     | Test Description                    | Expected Result               | Failure Conditions         | Test Type | Priority |
|-------------|------------------------------|-------------------------------------|-------------------------------|----------------------------|-----------|----------|
| TC-14       | Error Handling & Messages    | Trigger various failures            | Clear, friendly messages      | Silent or generic errors   | Manual    | Medium   |
| TC-13       | Reservation Time Window      | Too close to closing                | Valid slots only              | Booking outside hours      | Unit      | Medium   |
| TC-23 / TC-24 | Pre-order & Kitchen Cutoff | <30 min before needed/closing       | Blocked with message          | Order accepted             | Unit      | High     |

## Notes on Test Cases
* Test Type indicates the primary testing method recommended:
  * Unit → Automated (Pytest on models / forms / utils)
  * Integration → Automated (Pytest on views and database)
  * Manual → Browser / UI flows, role access, visual verification
* Each test case should be executed with positive, negative, and boundary data.
* During execution, record Actual Result, Status (Pass/Fail), and Evidence (screenshot/log).
* This table will be expanded further as more features are implemented.

## 10. Defect Tracking & User Acceptance Testing (UAT)

Defects will be tracked using GitHub Issues with appropriate labels (bug, priority, module, etc.).

### User Acceptance Testing (UAT) Cases

| UAT-ID | User Role       | Scenario                                              | Acceptance Criteria                              | Test Type |
|--------|-----------------|-------------------------------------------------------|--------------------------------------------------|-----------|
| UAT-01 | Customer        | End-to-end: Browse menu → Reserve → Order (dine-in) → Pay | Whole flow completes successfully                | Manual    |
| UAT-02 | Customer        | Delivery order with loyalty redemption                | Correct fee, address validation, points applied  | Manual    |
| UAT-03 | Server/Host     | Manage table status, take order, generate bill        | Fast and intuitive workflow                      | Manual    |
| UAT-04 | Kitchen Staff   | View incoming orders, update status                   | Orders appear in real-time, FIFO order           | Manual    |
| UAT-05 | Delivery Driver | Accept order, see details, mark delivered             | Only own orders visible, accurate info           | Manual    |
| UAT-06 | Manager/Owner   | View basic reports, manage menu & inventory           | Data is accurate and useful                      | Manual    |
| UAT-07 | Owner           | Role & location access across multiple restaurants    | Full visibility where appropriate                | Manual    |
| UAT-08 | All Users       | Usability & Error Messages                            | Navigation intuitive, errors helpful             | Manual    |
| UAT-09 | Customer (Guest)| Guest reservation + order                             | Works smoothly without account                   | Manual    |

## 11. References

* Scope Document (Scope Document - 25Apr2026)
* Entity-Relationship Diagram (ERD)
* Wireframes
