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
- Strong focus on input validation, boundary values, and business rules
- Identify defects early in development

## 2. Scope of Testing

### 2.1 In-Scope
- User registration, login, logout, and role-based access
- Restaurant setup, tables, menu items
- Reservations, ordering flows, order management
- Menu browsing, basic payment processing, loyalty points
- Input validation and error handling

### 2.2 Out-of-Scope
(See previous version)

## 3. Testing Approach

### 3.1 Types of Testing
- Unit Testing (individual functions and calculations)
- Integration Testing (multiple components working together)
- Functional and System Testing (end-to-end)
- User Interface and Usability Testing
- Manual Exploratory Testing
- Regression Testing
- Basic Security Testing

### 3.3 Automated Testing Considerations
Automated tests (Unit + Integration) will cover all critical business logic using **Pytest + pytest-django**.

## 9. Sample Test Cases

| Test ID   | Feature / Scenario                          | Test Description                                                                 | Expected Result (Pass)                                              | Failure Conditions                                              | Test Type       | Priority |
|-----------|---------------------------------------------|----------------------------------------------------------------------------------|---------------------------------------------------------------------|-----------------------------------------------------------------|-----------------|----------|
| TC-01     | User Registration                           | Attempt registration with valid + invalid data                                   | Account created with correct role                                   | Duplicate email, invalid format, missing fields                 | Integration     | High     |
| TC-02     | Role-based Login & Access                   | Login as each role and attempt restricted actions                                | User sees only permitted features                                   | Unauthorized access allowed                                     | Manual          | High     |
| TC-03     | Create Reservation                          | Valid/invalid times, overlapping tables                                          | Reservation created + table status updated                          | Overlapping, past time, invalid party size                      | Integration     | High     |
| TC-04     | Table Status Management                     | Update table status through normal flow                                          | Status updates correctly and consistently                           | Invalid status transitions                                      | Integration     | High     |
| TC-05     | Dine-in Order Creation                      | Add items to table order, send to kitchen                                        | Order created, sent to kitchen                                      | Order with no items, non-existent item                          | Integration     | High     |
| TC-06     | Delivery Order – Address Validation         | Create delivery order with/without address                                       | Order succeeds only with valid address                              | No address → blocked                                            | Unit            | High     |
| TC-07     | Loyalty Points Redemption – Over-Redemption | Apply $20 points on $10 order                                                    | System prevents over-redemption                                     | Negative total allowed                                          | Unit            | High     |
| TC-08     | Menu Item Price Validation                  | Negative price, zero price, non-numeric                                          | Only positive numeric prices accepted                               | Negative/zero/text accepted                                     | Unit            | High     |
| TC-09     | Quantity Validation                         | Quantity 0, negative, decimal, very large                                        | Only positive integers accepted                                     | Invalid quantities accepted                                     | Unit            | High     |
| TC-10     | Guest Checkout                              | Place order as guest (no account)                                                | Order succeeds without login                                        | Critical fields missing                                         | Integration     | High     |
| TC-11     | Order Total & Payment Calculation           | Add items, apply discount/points                                                 | Correct total, tax, and final amount                                | Negative totals, incorrect rounding                             | Unit            | High     |
| TC-12     | Menu Item Availability                      | Attempt to order unavailable item                                                | Item cannot be added                                                | Out-of-stock item is orderable                                  | Integration     | Medium   |
| TC-13     | Reservation Time Window                     | Book outside hours or too close to closing                                       | Only valid time slots allowed                                       | Booking outside hours                                           | Unit            | Medium   |
| TC-14     | Error Handling & Messages                   | Trigger various validation failures                                              | Clear, user-friendly error messages                                 | Silent or generic errors                                        | Manual          | Medium   |
| TC-15     | Loyalty Points Earning                      | Complete order and verify points added                                           | Points calculated and added correctly                               | Points not awarded correctly                                    | Unit            | Medium   |
| TC-16     | Location Toggle                             | Deactivate restaurant and attempt actions                                        | Customers cannot perform actions when inactive                      | Customers can still act                                         | Integration     | Medium   |
| TC-17     | Reservation: Conflict Detection             | Book already reserved table within next hour                                     | Booking rejected                                                    | Double booking allowed                                          | Unit            | High     |
| TC-18     | Cancellation Fee: Free Window               | Cancel 3+ hours before                                                           | No fee charged                                                      | Fee applied incorrectly                                         | Unit            | High     |
| TC-19     | Cancellation Fee: Within 3 hours            | Cancel less than 3 hours before                                                  | $10 fee applied                                                     | Fee not applied                                                 | Unit            | High     |
| TC-20     | Delivery Fee: 5km Tier                      | Delivery within 5km                                                              | Fee = $5.00                                                         | Wrong fee                                                       | Unit            | High     |
| TC-21     | Delivery Fee: 10km Tier                     | Delivery 5–10km                                                                  | Fee = $10.00                                                        | Wrong fee                                                       | Unit            | High     |
| TC-22     | Delivery Fee: Beyond 10km                   | Delivery >10km                                                                   | Delivery rejected                                                   | Delivery allowed                                                | Unit            | High     |
| TC-23     | Pre-Order: Cutoff Enforcement               | Order less than 30 min before needed                                             | Order blocked                                                       | Order accepted                                                  | Unit            | High     |
| TC-24     | Kitchen: Order Cutoff                       | Order near closing time                                                          | Order blocked                                                       | Order accepted                                                  | Unit            | High     |
| TC-25     | Loyalty Points: Correct Tier Redemption     | Redeem 1000 pts on $15 order                                                     | $10 discount applied                                                | Wrong discount                                                  | Unit            | High     |
| TC-26     | Loyalty Points: Partial Redemption Blocked  | Redeem 500 pts (below tier)                                                      | Redemption blocked                                                  | Partial redemption allowed                                      | Unit            | High     |
| TC-27     | Loyalty Points: Max Discount Cap            | Redeem 2000 pts on $30 order                                                     | Max $25 discount applied                                            | Discount exceeds $25                                            | Unit            | High     |
| TC-28     | Role Access: Kitchen Staff                  | Kitchen staff tries to access reservations                                       | Access denied                                                       | Access granted                                                  | Manual          | High     |
| TC-29     | Role Access: Delivery Driver                | Driver views another driver’s orders                                             | Access denied                                                       | Access granted                                                  | Manual          | High     |
| TC-30     | Role Access: Server / Host                  | Server tries to access inventory                                                 | Access denied                                                       | Access granted                                                  | Manual          | High     |
| TC-31     | Guest Reservation: Deposit Required         | Guest reservation without deposit                                                | Reservation blocked                                                 | Accepted without deposit                                        | Integration     | High     |
| TC-32     | Table Status: Valid Transition              | Update table from Empty to Occupied                                              | Status updates correctly                                            | Invalid transition accepted                                     | Integration     | High     |
| TC-33     | Table Status: Invalid Transition            | Set undefined status                                                             | Request rejected                                                    | Invalid status saved                                            | Unit            | High     |
| TC-34     | Menu Item: Image Upload                     | Upload with and without image                                                    | Item saves correctly                                                | Fails without image                                             | Integration     | High     |
| TC-35     | CSV Menu: Upload Validation                 | Valid and invalid CSV                                                            | Valid imports, invalid rejected                                     | Invalid imports                                                 | Integration     | High     |
| TC-36     | Loyalty Points: Earning Calculation         | $50 order                                                                        | 500 points awarded (excl. tax)                                      | Wrong calculation                                               | Unit            | High     |
| TC-37     | Reservation: Party Size Limit               | Book for 21+ people                                                              | Booking rejected                                                    | Booking accepted                                                | Unit            | High     |
| TC-38     | Reservation: Past Date/Time                 | Book in the past                                                                 | Booking rejected                                                    | Accepted                                                        | Unit            | High     |
| TC-39     | Reservation: Outside Operating Hours        | Book outside hours                                                               | Booking rejected                                                    | Accepted                                                        | Unit            | High     |
| TC-40     | Reservation: Deposit Amount                 | Verify deposit charged                                                           | Exactly $10 charged                                                 | Wrong amount                                                    | Unit            | High     |
| TC-41     | Order: Cancel after Commit                  | Edit order after submission                                                      | Edit blocked                                                        | Editing allowed                                                 | Integration     | High     |
| TC-42     | Order: Empty Cart Checkout                  | Submit order with no items                                                       | Checkout blocked                                                    | Empty order submitted                                           | Integration     | High     |
| TC-43     | Order: Unavailable Menu Item                | Add unavailable item                                                             | Item cannot be added                                                | Item added                                                      | Integration     | High     |
| TC-44     | Order: Special Instructions                 | Add instructions to order item                                                   | Visible on kitchen dashboard                                        | Not saved/displayed                                             | Integration     | Medium   |
| TC-45     | Payment: Visa and Mastercard Only           | Use unsupported payment method                                                   | Payment blocked                                                     | Unsupported method accepted                                     | Unit            | High     |
| TC-46     | Payment: Auto Approval                      | Valid Visa/Mastercard checkout                                                   | Payment approved                                                    | Payment rejected                                                | Integration     | High     |
| TC-47     | Loyalty Points: Guest Account               | Order as guest                                                                   | No points awarded                                                   | Points awarded                                                  | Unit            | High     |
| TC-48     | Loyalty Points: Tax Exclusion               | $50 + $5 tax order                                                               | Points on subtotal only                                             | Points on total incl. tax                                       | Unit            | Medium   |
| TC-49     | Loyalty Points: No Expiry                   | Check points after inactivity                                                    | Points remain                                                       | Points expire                                                   | Unit            | Medium   |
| TC-50     | Delivery: Geocoding Fallback                | Simulate geocoding failure                                                       | Fallback works                                                      | Checkout blocked                                                | Integration     | High     |
| TC-51     | Delivery: Driver Sees Own Orders Only       | Login as driver                                                                  | Only own orders visible                                             | Sees all orders                                                 | Manual          | High     |
| TC-52     | Delivery: Order Details Accuracy            | Check driver order view                                                          | All details match                                                   | Details missing/incorrect                                       | Manual          | High     |
| TC-53     | Kitchen: FIFO Order                         | Place three orders                                                               | Oldest first on dashboard                                           | Wrong order                                                     | Integration     | High     |
| TC-54     | Kitchen: Status Progression                 | Update order status step-by-step                                                 | Each status saves correctly                                         | Status skips                                                    | Integration     | High     |
| TC-55     | Inventory: Low Stock Alert                  | Set below minimum                                                                | Alert shown to manager only                                         | Alert not triggered                                             | Integration     | High     |
| TC-56     | Inventory: Min/Max Level Setting            | Manager sets levels                                                              | Levels saved and used                                               | Not saved / wrong threshold                                     | Integration     | Medium   |
| TC-57     | Inventory: Non-Manager Access               | Non-manager accesses inventory                                                   | Access denied                                                       | Access granted                                                  | Manual          | High     |
| TC-58     | Server: POS Order on Behalf of Customer     | Server places dine-in order                                                      | Order linked and sent to kitchen                                    | Not linked / not sent                                           | Integration     | High     |
| TC-59     | Server: Bill Generation                     | Generate bill for table                                                          | Bill shows correct data                                             | Incorrect data                                                  | Manual          | High     |
| TC-60     | Registration: Duplicate Email               | Register with existing email                                                     | Blocked with error                                                  | Duplicate created                                               | Integration     | High     |
| TC-61     | Registration: Missing Required Fields       | Submit with missing fields                                                       | Field-specific errors                                               | Incomplete account created                                      | Integration     | High     |
| TC-62     | Login: Wrong Password                       | Login with wrong password                                                        | Rejected with error                                                 | Login succeeds                                                  | Integration     | High     |
| TC-63     | Owner: Cross-Location Access                | Owner logs in                                                                    | Can access all locations                                            | Restricted to one location                                      | Manual          | High     |

## 9.1 Test Case Notes
- Each test case should be executed with **positive**, **negative**, and **boundary** data.
- **Test Type** indicates the primary testing method recommended:
  - **Unit** → Automated (Pytest on models/forms/utils)
  - **Integration** → Automated (Pytest on views + database)
  - **Manual** → Browser / UI flows, role access, visual verification
- Record **Actual Result**, **Status**, and **Evidence** during execution.


## 10. Defect Tracking
Defects will be tracked using **GitHub Issues** with appropriate labels (bug, priority, module, etc.). Each issue should include:

- Steps to reproduce
- Expected vs actual result
- Screenshots or logs (when possible)

## 11. References
- Scope Document (Scope Document - 25Apr2026)
- Entity-Relationship Diagram (ERD)
- Wireframes

