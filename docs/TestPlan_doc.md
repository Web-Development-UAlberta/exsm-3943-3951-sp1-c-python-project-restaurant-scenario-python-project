# Test Plan - Restaurant Management System

**Version:** 1.0 (Draft)  
**Date:** April 21, 2026  
**Prepared by:** Michael Hubel  
**Project:** Restaurant Management System

## 1. Introduction

### 1.1 Purpose
This Test Plan describes the overall testing strategy, scope, approach, resources, and schedule for the Restaurant Management System. It ensures the system functions correctly according to the requirements in the Scope Document.

### 1.2 Project Overview
The Restaurant Management System is a web application that allows customers to make reservations, browse the menu, and place orders for dine-in, takeout, or delivery. Staff members (servers, kitchen staff, managers, delivery drivers, and owners) can manage tables, reservations, orders, and basic operations. The system also includes loyalty points tracking.

### 1.3 Testing Objectives

- Verify all in-scope features work as expected
- Ensure proper role-based access control for different user types
- Validate critical end-to-end flows (reservation, ordering, payment)
- Check data consistency (orders, table status, loyalty points)
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
- Advanced analytics and reporting
- Real external payment gateway or delivery service integration
- Performance and load testing
- Mobile application testing (web only)
- Advanced visual floor plan editor

## 3. Testing Approach

### 3.1 Types of Testing

- Unit Testing (individual functions and calculations)
- Integration Testing (e.g., Order + OrderItem + Payment)
- Functional and System Testing (end-to-end user scenarios)
- User Interface and Usability Testing
- Manual Exploratory Testing
- Regression Testing after changes
- Basic Security Testing (authentication, input validation)

### 3.2 Testing Method
Primarily manual testing for this phase. Automated tests may be introduced in future iterations.

## 4. Test Environment

- Local development environment (Django + PostgreSQL or chosen stack)
- Docker-based setup (if applicable)
- Browsers: Chrome and Firefox (latest versions)
- Test Data: Sample users with different roles, restaurants, menus, tables, and orders

## 5. Test Schedule

- Test Plan Draft: April 21–22, 2026
- Detailed Test Case Development: [Insert Date]
- Initial Test Execution: [Insert Date]
- Bug Fixing and Retesting: [Insert Date]
- Final Test Report: [Before project deadline]

## 6. Roles and Responsibilities

- **Test Coordinator:** [Name]
- **Testers:** All group members
- **Developers:** Fix reported issues
- **Reviewer:** Whole group

## 7. Risks and Mitigation

- **Risk:** Changing requirements  
  **Mitigation:** Cross-check with Scope Document and ERD regularly

- **Risk:** Lack of realistic test data  
  **Mitigation:** Prepare seed data early

- **Risk:** Time constraints  
  **Mitigation:** Prioritize critical paths (login → reservation → order → payment)

- **Risk:** Role-based permission issues  
  **Mitigation:** Test each feature with multiple roles

## 8. Entry and Exit Criteria

- **Entry Criteria:** Scope Document finalized, ERD Revision 1 complete, core features under development
- **Exit Criteria:** All high-priority test cases passed, major defects resolved or documented

## 9. Sample Test Cases

| Test ID | Feature                    | Pass                                                    | Fail                                                      | Priority |
|---------|----------------------------|---------------------------------------------------------|-----------------------------------------------------------|----------|
| TC-01   | User Registration          | Successful account creation                             | Invalid data or duplicate email                           | High     |
| TC-02   | Role-based Login           | User sees only permitted features                       | Login fails or sees unauthorized features                 | High     |
| TC-03   | Create Reservation         | Reservation created + table marked occupied             | Table in use, invalid time, or excessive duration         | High     |
| TC-04   | Table Status Management    | Table status updates correctly                          | Status fails to update                                    | High     |
| TC-05   | Dine-in Order              | Order created + sent to kitchen + ticket generated      | Order creation fails                                      | High     |
| TC-06   | Delivery Order             | Order created + ETA displayed                           | Order creation fails                                      | High     |
| TC-07   | Loyalty Points             | Points visible and redeemable                           | Cannot access or redeem points                            | Medium   |
| TC-08   | Error Handling             | Appropriate error messages shown                        | No or wrong error messages                                | Medium   |
| TC-09   | Guest Checkout             | Guest can place order successfully                      | Order fails for guest user                                | High     |

> **Note:** This table will be expanded with full steps, actual results, and status during test execution.

## 10. Defect Tracking
Defects will be tracked using GitHub Issues with appropriate labels (bug, priority, module, etc.). Each issue should include:

- Steps to reproduce
- Expected vs actual result
- Screenshots or logs (when possible)

## 11. References

- Scope Document (Scope Document - 15Apr2026)
- Entity-Relationship Diagram (ERD)
- Wireframes