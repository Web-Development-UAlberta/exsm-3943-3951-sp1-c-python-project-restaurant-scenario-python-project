# Test Plan - Restaurant Management System

**Version:** 1.1 (Updated)  
**Date:** April 25, 2026  
**Prepared by:** Michael Hubel  
**Project:** Restaurant Management System

## 1. Introduction

### 1.1 Purpose
This Test Plan describes the overall testing strategy, scope, approach, resources, and schedule for the Restaurant Management System. It ensures the system functions correctly according to the requirements in the Scope Document, with strong emphasis on input validation, business rules, and edge-case handling.

### 1.2 Project Overview
The Restaurant Management System is a web application that allows customers to make reservations, browse the menu, and place orders for dine-in, takeout, or delivery. Staff members (servers, kitchen staff, managers, delivery drivers, and owners) can manage tables, reservations, orders, and basic operations. The system also includes loyalty points tracking.

### 1.3 Testing Objectives

- Verify all in-scope features work as expected
- Ensure proper role-based access control for different user types
- Validate critical end-to-end flows (reservation, ordering, payment)
- Check data consistency (orders, table status, loyalty points)
- Strong focus on input validation, boundary values, and "what is allowed vs. not allowed"
- Identify defects early in development

## 2. Scope of Testing

### 2.1 In-Scope

- User registration, login, logout, and role-based access (customer, server, kitchen_staff, delivery_driver, manager, owner, guest)
- Restaurant basic setup (information, tables, menu items)
- Reservations (create, view, status updates: confirmed → seated → completed/cancelled)
- Ordering flows (dine-in with table, takeout, delivery with address)
- Order management and status updates
- Menu browsing and item selection
- Basic payment processing
- Loyalty points earning and redeeming
- Input validation and basic error handling

### 2.2 Out-of-Scope

- Full inventory management with recipe linking
- Advanced analytics and reporting (Basic reporting is included — menu item sales, ingredient usage summaries, etc.; complex dashboards, trend forecasting, and data exports are out of scope)
- Real external payment gateway or delivery service integration
- Performance and load testing
- Mobile application testing (web only)
- CSV based floor plan uploads (Table layout is managed through the built-in visual grid interface only)

## 3. Testing Approach

### 3.1 Types of Testing

- Unit Testing (individual functions and calculations)
- Integration Testing (e.g., Order + OrderItem + Payment + Loyalty)
- Functional and System Testing (end-to-end user scenarios)
- User Interface and Usability Testing
- Manual Exploratory Testing
- Regression Testing after changes
- Basic Security Testing (authentication, input validation, authorization)

### 3.2 Testing Method

- **Automated testing** using Pytest and pytest-django is the primary approach for all critical business logic.
- **Manual testing** covers UI flows, usability, and exploratory scenarios.
- GitHub Actions runs the full test suite automatically on every push to main and every pull request.

### 3.3 Automated Testing Considerations
Key validation rules and business logic will be automated to catch regressions quickly (address validation, loyalty points, price rules, reservation conflicts, fees, cutoffs, role enforcement, etc.).

## 4. Test Environment

- Local development environment (Django + SQLite)
- Docker-based setup (if applicable)
- Browsers: Chrome and Firefox (latest versions)
- Test Data: Sample users with different roles, restaurants, menus, tables, and orders
- pytest-django test database (separate SQLite instance, auto-created and torn down per test run)

## 5. Test Schedule

- Test Plan Draft: April 21–25, 2026
- Detailed Test Case Development: A detailed and organized testing schedule will be discussed and created following weekly requirements and tasks.
- Initial Test Execution: Commenced as features are complete and working
- Bug Fixing and Retesting: Phase after features are complete (includes feedback implementation and bug fixes)
- Final Test Report: Before May 25th, 2026 (in time for the “release candidate”)

## 6. Roles and Responsibilities

**Test Coverage Goals:** 100% coverage on all critical business logic functions and +80% overall codebase coverage.

- **Test Coordinator:** Michael
- **Testers:** All group members
- **Developers:** Fix reported issues
- **Reviewer:** Whole group

## 7. Risks and Mitigation

- **Risk:** Changing requirements → **Mitigation:** Cross-check with Scope Document and ERD regularly
- **Risk:** Lack of realistic test data → **Mitigation:** Prepare seed data early
- **Risk:** Time constraints → **Mitigation:** Prioritize critical paths (login → reservation → order → payment)
- **Risk:** Role-based permission issues → **Mitigation:** Test each feature with multiple roles

## 8. Entry and Exit Criteria

- **Entry Criteria:** Scope Document finalized, ERD Revision 1 complete, core features under development
- **Exit Criteria:** All high-priority test cases passed, major defects resolved or documented

## 9. Sample Test Cases

| Test ID | Feature / Scenario                    | Test Description                                              | Expected Result (Pass)                                      | Failure Conditions                                              | Test Type     | Priority |
|---------|---------------------------------------|---------------------------------------------------------------|-------------------------------------------------------------|-----------------------------------------------------------------|---------------|----------|
| TC-01   | User Registration                     | Attempt registration with valid + invalid data                | Account created with correct role                           | Duplicate email, invalid format, missing fields                 | Integration   | High     |
| TC-02   | Role-based Login & Access             | Login as each role and attempt restricted actions             | User sees only permitted features                           | Unauthorized access                                             | Manual        | High     |
| TC-03   | Create Reservation                    | Create reservation with valid/invalid times, overlapping      | Reservation created + table status updated                  | Overlapping booking, past time, invalid party size              | Integration   | High     |
| TC-04   | Table Status Management               | Update table status through normal flow                       | Status updates correctly and consistently                   | Invalid status transitions                                      | Integration   | High     |
| TC-05   | Dine-in Order Creation                | Add items to table order, send to kitchen                     | Order created, sent to kitchen, ticket generated            | Order with no items, non-existent menu item                     | Integration   | High     |
| TC-06   | Delivery Order – Address Validation   | Create delivery order with full address                       | Order succeeds only when valid address is provided          | No address or incomplete address → blocked                      | Unit          | High     |
| TC-07   | Loyalty Points Redemption – Over-Redemption | Apply reward points worth more than order total         | System prevents redemption or caps at order total           | Negative total allowed                                          | Unit          | High     |
| TC-08   | Menu Item Price Validation            | Attempt negative price, zero price, non-numeric               | Only positive numeric prices accepted                       | Negative, zero, or text values blocked                          | Unit          | High     |
| TC-09   | Quantity Validation                   | Add item with quantity 0, negative, decimal                   | Only positive integers accepted                             | 0, negative, or non-integer quantities blocked                  | Unit          | High     |
| TC-10   | Guest Checkout                        | Place order as guest (no account)                             | Order succeeds without login                                | Critical fields missing for guest                               | Integration   | High     |
| TC-11   | Order Total & Payment Calculation     | Add items, apply discount/points, verify total                | Correct total, tax, and final amount                        | Negative totals, incorrect rounding                             | Unit          | High     |
| TC-12   | Menu Item Availability                | Attempt to order item marked "out of stock"                   | Item cannot be added to order                               | Out-of-stock item is orderable                                  | Integration   | Medium   |
| TC-13   | Reservation Time Window               | Try to book outside restaurant hours                          | Only valid time slots allowed                               | Booking outside operating hours                                 | Unit          | Medium   |
| TC-14   | Error Handling & Messages             | Trigger various validation failures                           | Clear, user-friendly error messages shown                   | Silent failures or generic errors                               | Manual        | Medium   |
| TC-15   | Loyalty Points Earning                | Complete order and verify points are added                    | Points calculated and added correctly                       | Points not awarded or awarded incorrectly                       | Unit          | Medium   |
| TC-16   | Location Toggle                       | Deactivate restaurant and attempt customer actions            | Restaurant is “inactive”                                    | Customers can still perform actions                             | Integration   | Medium   |
| TC-17   | Reservation: Conflict Detection       | Attempt to book already reserved table                        | Booking rejected with clear error                           | Double booking allowed                                          | Unit          | High     |
| TC-18   | Cancellation Fee: Free Window         | Cancel reservation 3+ hours before                            | Cancellation succeeds, no fee                               | Fee applied incorrectly                                         | Unit          | High     |
| TC-19   | Cancellation Fee: Within 3 hours      | Cancel reservation less than 3 hours before                   | $10 cancellation fee applied                                | Fee not applied or wrong amount                                 | Unit          | High     |
| TC-20   | Delivery Fee: 5km Tier                | Delivery address within 5km                                   | Delivery fee = $5.00                                        | Wrong fee applied or delivery blocked                           | Unit          | High     |
| TC-21   | Delivery Fee: 10km Tier               | Delivery address between 5km and 10km                         | Delivery fee = $10.00                                       | Wrong fee applied                                               | Unit          | High     |
| TC-22   | Delivery Fee: Beyond 10km             | Delivery address beyond 10km                                  | Delivery rejected                                           | Delivery allowed beyond range                                   | Unit          | High     |
| TC-23   | Pre-Order: Cutoff Enforcement         | Place order less than 30 minutes before needed time           | Order blocked with clear error                              | Order accepted within cutoff window                             | Unit          | High     |
| TC-24   | Kitchen: Order Cutoff                 | Place order within 30 minutes of closing                      | Order blocked, system shows closed message                  | Order accepted near closing                                     | Unit          | High     |
| TC-25   | Loyalty Points: Correct Tier Redemption | Redeem exactly 1000 points on a $15 order                   | $10 discount applied, 1000 points deducted                  | Wrong discount or wrong points deducted                         | Unit          | High     |
| TC-26   | Loyalty Points: Partial Redemption Blocked | Attempt to redeem 500 points (below minimum tier)        | Redemption blocked, error shown                             | Partial redemption allowed                                      | Unit          | High     |
| TC-27   | Loyalty Points: Max Discount Cap      | Redeem 2000 points on a $30 order                             | $25 discount applied, total = $5                            | Discount exceeds $25                                            | Unit          | High     |
| TC-28   | Role Access: Kitchen Staff            | Kitchen staff attempts reservations page                      | Access denied, redirected                                   | Kitchen staff can view customer data                            | Manual        | High     |
| TC-29   | Role Access: Delivery Driver          | Delivery driver views another driver’s orders                 | Access denied                                               | Driver sees other driver’s orders                               | Manual        | High     |
| TC-30   | Role Access: Server / Host            | Server attempts inventory management                          | Access denied                                               | Server can access manager-only views                            | Manual        | High     |
| TC-31   | Guest Reservation: Deposit Required   | Complete reservation as guest without deposit                 | Reservation blocked until deposit confirmed                 | Guest reservation accepted without deposit                      | Integration   | High     |
| TC-32   | Table Status: Valid Transition        | Server updates table from “Empty” to “Occupied”               | Status updates correctly                                    | Invalid status accepted                                         | Integration   | High     |
| TC-33   | Table Status: Invalid Transition      | Attempt to set table status to an undefined value             | Request rejected                                            | Invalid status saved to database                                | Unit          | High     |
| TC-34   | Menu Item: Image Upload               | Upload menu item with and without image                       | Item saves correctly, Image_path null when no image         | Item fails to save without image                                | Integration   | High     |
| TC-35   | CSV Menu: Upload Validation           | Upload valid CSV and invalid CSV                              | Valid CSV imports correctly, invalid rejected               | Invalid CSV imports silently                                    | Integration   | High     |
| TC-36   | Loyalty Points: Earning Calculation   | Complete a $50 order                                          | Customer receives 500 points (10 per dollar, excl. tax)     | Wrong points calculation                                        | Unit          | High     |
| TC-37   | Reservation: Party Size Limit         | Book for 21 or more people                                    | Booking rejected, contact restaurant                        | Booking accepted above 20 people                                | Unit          | High     |
| TC-38   | Reservation: Past Date/Time           | Book for a date/time in the past                              | Booking rejected with clear error                           | Past bookings accepted                                          | Unit          | High     |
| TC-39   | Reservation: Outside Operating Hours  | Book outside opening/closing times                            | Booking rejected                                            | Booking accepted outside hours                                  | Unit          | High     |
| TC-40   | Reservation: Deposit Amount           | Complete a reservation                                        | Deposit = exactly $10                                       | Wrong deposit amount or no deposit                              | Unit          | High     |
| TC-41   | Order: Cancel after Commit            | Attempt to edit order after submission                        | Edit blocked, only cancellation allowed                     | Order editable after submission                                 | Integration   | High     |
| TC-42   | Order: Empty Cart Checkout            | Submit order with no items                                    | Checkout blocked with clear error                           | Empty order submitted                                           | Integration   | High     |
| TC-43   | Order: Unavailable Menu Item          | Add item marked unavailable                                   | Item cannot be added, error shown                           | Unavailable item added                                          | Integration   | High     |
| TC-44   | Order: Special Instructions           | Add special instructions to order item                        | Instructions visible on kitchen dashboard                   | Instructions not saved or displayed                             | Integration   | Medium   |
| TC-45   | Payment: Visa and Mastercard Only     | Attempt checkout with unsupported method                      | Payment blocked, only Visa/Mastercard accepted              | Unsupported method accepted                                     | Unit          | High     |
| TC-46   | Payment: Auto Approval                | Complete checkout with valid Visa/Mastercard                  | Payment always approved, confirmation shown                 | Payment rejected or stuck                                       | Integration   | High     |
| TC-47   | Loyalty Points: Guest Account         | Complete order as guest                                       | No points awarded                                           | Points awarded to guest account                                 | Unit          | High     |
| TC-48   | Loyalty Points: Tax Exclusion         | Complete $50 order with $5 tax                                | Points earned on $50 subtotal only                          | Points calculated on total including tax                        | Unit          | Medium   |
| TC-49   | Loyalty Points: No Expiry             | Points remain after long inactivity                           | Points balance remains unchanged                            | Points expire or reset                                          | Unit          | Medium   |
| TC-50   | Delivery: Geocoding Fallback          | Simulate geocoding failure                                    | Fallback dropdown appears                                   | Checkout blocked entirely                                       | Integration   | High     |
| TC-51   | Delivery: Driver Sees Own Orders Only | Log in as driver                                              | Only their assigned orders visible                          | Driver sees all delivery orders                                 | Manual        | High     |
| TC-52   | Delivery: Order Details Accuracy      | Verify driver view                                            | All details match the order record                          | Missing or incorrect details                                    | Manual        | High     |
| TC-53   | Kitchen: FIFO Order                   | Place three orders in sequence                                | Orders displayed oldest first                               | Orders shown out of sequence                                    | Integration   | High     |
| TC-54   | Kitchen: Status Progression           | Update order through statuses                                 | Each status update saves correctly                          | Status skips or saves incorrectly                               | Integration   | High     |
| TC-55   | Inventory: Low Stock Alert            | Set ingredient below minimum                                  | Low stock flag triggered, alert visible to manager          | Alert not triggered or wrong roles                              | Integration   | High     |
| TC-56   | Inventory: Min/Max Level Setting      | Manager sets min/max levels                                   | Levels saved correctly                                      | Levels not saved or wrong threshold                             | Integration   | Medium   |
| TC-57   | Inventory: Non-Manager Access         | Non-manager attempts inventory                                | Access denied                                               | Non-manager can view/edit                                       | Manual        | High     |
| TC-58   | Server: POS Order on Behalf of Customer | Server places dine-in order through floor view            | Order created and sent to kitchen correctly                 | Order not linked to correct table                               | Integration   | High     |
| TC-59   | Server: Bill Generation               | Server generates bill for a table                             | Bill shows correct data                                     | Bill shows incorrect data or fails                              | Manual        | High     |
| TC-60   | Registration: Duplicate Email         | Register with existing email                                  | Registration blocked with clear error                       | Duplicate account created                                       | Integration   | High     |
| TC-61   | Registration: Missing Required Fields | Submit form with missing fields                               | Field-specific errors shown                                 | Incomplete account created                                      | Integration   | High     |
| TC-62   | Login: Wrong Password                 | Login with incorrect password                                 | Login rejected, error shown                                 | Login succeeds with wrong password                              | Integration   | High     |
| TC-63   | Owner: Cross-Location Access          | Owner logs in                                                 | Owner sees all restaurant locations                         | Owner restricted to one location                                | Manual        | High     |

> **Note:** Each test case should be executed with positive, negative, and boundary data. During execution, record Actual Result, Status (Pass/Fail), and Evidence (screenshot/log). This table will continue to expand as more features are implemented.

**Test Type Legend:**
- **Unit** → Automated (Pytest on models/forms/utils)
- **Integration** → Automated (Pytest on views/database)
- **Manual** → Browser/UI flows, role access, visual checks

## 10. Defect Tracking
Defects will be tracked using GitHub Issues with appropriate labels (bug, priority, module, etc.). Each issue should include:

- Steps to reproduce
- Expected vs actual result
- Screenshots or logs (when possible)

## 11. References

- Scope Document (Scope Document - 25Apr2026)
- Entity-Relationship Diagram (ERD)
- Wireframes