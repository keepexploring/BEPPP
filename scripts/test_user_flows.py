#!/usr/bin/env python3
"""
Integration test script for user flows: user CRUD with new fields,
battery/PUE rental lifecycle, deposit hold system, upfront payments,
and decimal duration cost structures.

Requires a running backend with at least one hub and a superadmin user.

Usage:
    python scripts/test_user_flows.py
    python scripts/test_user_flows.py http://localhost:8000 admin_username admin_password
"""

import requests
import json
import os
import sys
from datetime import datetime, timedelta, timezone

# Configuration
API_BASE_URL = sys.argv[1] if len(sys.argv) > 1 else os.environ.get("API_URL", "http://localhost:8000")
ADMIN_USERNAME = sys.argv[2] if len(sys.argv) > 2 else os.environ.get("TEST_ADMIN_USER", "admin")
ADMIN_PASSWORD = sys.argv[3] if len(sys.argv) > 3 else os.environ.get("TEST_ADMIN_PASS", "admin")

passed = 0
failed = 0
created_ids = {}  # Track created resources for cleanup


def section(title):
    print(f"\n{'='*60}\n  {title}\n{'='*60}")


def check(name, condition, detail=""):
    global passed, failed
    if condition:
        passed += 1
        print(f"  PASS  {name}")
    else:
        failed += 1
        print(f"  FAIL  {name}")
    if detail:
        print(f"        {detail}")


def get_token():
    """Authenticate as admin and return JWT token."""
    r = requests.post(f"{API_BASE_URL}/auth/token", json={
        "username": ADMIN_USERNAME,
        "password": ADMIN_PASSWORD
    })
    if r.status_code != 200:
        print(f"FATAL: Cannot authenticate as {ADMIN_USERNAME}. Status: {r.status_code}")
        print(f"  Response: {r.text[:500]}")
        print(f"  Set TEST_ADMIN_USER and TEST_ADMIN_PASS env vars or pass as CLI args.")
        sys.exit(1)
    data = r.json()
    token = data.get("access_token") or data.get("token")
    if not token:
        print(f"FATAL: No token in response: {json.dumps(data)[:200]}")
        sys.exit(1)
    return token


def headers(token):
    return {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}


# ============================================================================
# 1. Authentication
# ============================================================================
section("1. Authentication")
token = get_token()
check("Login and get token", bool(token))

# Get hub_id from hubs endpoint
r = requests.get(f"{API_BASE_URL}/hubs", headers=headers(token))
if r.status_code in [200, 307]:
    # Handle redirect
    if r.status_code == 307:
        r = requests.get(f"{API_BASE_URL}/hubs/", headers=headers(token))
    hubs = r.json()
    hub_id = hubs[0]["hub_id"] if hubs else 1
    check("Get hub ID", True, f"hub_id={hub_id}")
else:
    hub_id = 1
    check("Get hub ID", True, f"Using default hub_id={hub_id}")


# ============================================================================
# 2. User CRUD with new fields
# ============================================================================
section("2. User CRUD with new fields")

# 2a. Create user with multi-select fields and energy split
test_user_data = {
    "first_names": "Test",
    "last_name": "FlowUser",
    "mobile_number": "+1234567890",
    "hub_id": hub_id,
    "user_access_level": "user",
    "username": f"testflow_{int(datetime.now(timezone.utc).timestamp())}",
    "password": "TestFlow1!",
    "gesi_status": ["Youth (<18)", "Female"],
    "main_reason_for_signup": ["Lighting", "Phone Charging"],
    "monthly_energy_electricity": 50.0,
    "monthly_energy_heat": 30.0,
    "business_category": "Small Business"
}

r = requests.post(f"{API_BASE_URL}/users/", json=test_user_data, headers=headers(token))
check("Create user with multi-select fields", r.status_code == 200, f"Status: {r.status_code}")

if r.status_code == 200:
    user_response = r.json()
    user_data = user_response.get("user", user_response)
    test_user_id = user_data.get("user_id")
    created_ids["user_id"] = test_user_id
    check("User ID assigned", bool(test_user_id), f"user_id={test_user_id}")

    # Check gesi_status returned as list
    gesi = user_data.get("gesi_status")
    check("gesi_status returned as list", isinstance(gesi, list), f"gesi_status={gesi}")
    check("gesi_status has 2 items", isinstance(gesi, list) and len(gesi) == 2, f"len={len(gesi) if isinstance(gesi, list) else 'N/A'}")

    # Check main_reason_for_signup returned as list
    signup = user_data.get("main_reason_for_signup")
    check("main_reason_for_signup as list", isinstance(signup, list), f"main_reason_for_signup={signup}")

    # Check energy split computed
    expenditure = user_data.get("monthly_energy_expenditure")
    check("monthly_energy_expenditure computed (50+30=80)", expenditure == 80.0, f"expenditure={expenditure}")
    check("monthly_energy_electricity stored", user_data.get("monthly_energy_electricity") == 50.0)
    check("monthly_energy_heat stored", user_data.get("monthly_energy_heat") == 30.0)

    # 2b. GET user - verify fields
    r = requests.get(f"{API_BASE_URL}/users/{test_user_id}", headers=headers(token))
    check("GET user", r.status_code == 200)
    if r.status_code == 200:
        fetched = r.json()
        check("GET gesi_status is list", isinstance(fetched.get("gesi_status"), list))
        check("GET main_reason_for_signup is list", isinstance(fetched.get("main_reason_for_signup"), list))

    # 2c. Update user
    r = requests.put(f"{API_BASE_URL}/users/{test_user_id}", json={
        "gesi_status": ["Male"],
        "monthly_energy_electricity": 100.0
    }, headers=headers(token))
    check("Update user fields", r.status_code == 200, f"Status: {r.status_code}")
    if r.status_code == 200:
        updated = r.json()
        check("Updated gesi_status", updated.get("gesi_status") == "Male" or updated.get("gesi_status") == ["Male"])
        check("Updated energy expenditure (100+30=130)", updated.get("monthly_energy_expenditure") == 130.0,
              f"expenditure={updated.get('monthly_energy_expenditure')}")

    # 2d. Backward compat: string gesi_status
    r = requests.put(f"{API_BASE_URL}/users/{test_user_id}", json={
        "gesi_status": "Single Value"
    }, headers=headers(token))
    check("Backward compat: string gesi_status", r.status_code == 200)
else:
    test_user_id = None
    print("  SKIP  Skipping remaining user tests (create failed)")


# ============================================================================
# 3. Battery Rental Lifecycle with Deposit & Upfront Payment
# ============================================================================
section("3. Battery Rental Lifecycle")

if test_user_id:
    # 3a. Create cost structure with deposit and components (query params, components as JSON string)
    cs_params = {
        "name": "Test Battery CS",
        "hub_id": hub_id,
        "item_type": "battery_capacity",
        "item_reference": "all",
        "deposit_amount": 50.0,
        "components": json.dumps([
            {"component_name": "Daily Rate", "unit_type": "per_day", "rate": 10.0, "sort_order": 0}
        ])
    }
    r = requests.post(f"{API_BASE_URL}/settings/cost-structures", params=cs_params, headers=headers(token))
    check("Create cost structure", r.status_code == 200 or r.status_code == 201, f"Status: {r.status_code}")

    cs_id = None
    if r.status_code in [200, 201]:
        cs_response = r.json()
        cs_id = cs_response.get("structure_id") or cs_response.get("cost_structure_id")
        created_ids["cost_structure_id"] = cs_id
        check("Cost structure ID", bool(cs_id), f"structure_id={cs_id}")

    # 3b. Add credit to user account (so deposit hold can work)
    r = requests.post(f"{API_BASE_URL}/accounts/user/{test_user_id}/transaction", params={
        "amount": 200.0,
        "transaction_type": "credit",
        "description": "Test credit for deposit"
    }, headers=headers(token))
    check("Add credit to account", r.status_code == 200, f"Status: {r.status_code}")

    # 3c. Check credit summary
    r = requests.get(f"{API_BASE_URL}/accounts/user/{test_user_id}/credit-summary", headers=headers(token))
    check("Get credit summary", r.status_code == 200)
    if r.status_code == 200:
        summary = r.json()
        check("Credit summary has balance", summary.get("balance", 0) >= 200.0,
              f"balance={summary.get('balance')}")
        check("No held deposits yet", summary.get("held_deposits", 0) == 0)

    # 3d. Get a battery to rent
    r = requests.get(f"{API_BASE_URL}/hubs/{hub_id}/batteries", headers=headers(token))
    test_battery_id = None
    if r.status_code == 200:
        batteries = r.json()
        available = [b for b in batteries if b.get("status") == "available"]
        if available:
            test_battery_id = available[0]["battery_id"]
            check("Found available battery", True, f"battery_id={test_battery_id}")
        else:
            # Create a test battery
            r2 = requests.post(f"{API_BASE_URL}/batteries/", json={
                "battery_id": "TEST-FLOW-001",
                "hub_id": hub_id,
                "battery_capacity_wh": 1000,
                "status": "available"
            }, headers=headers(token))
            if r2.status_code in [200, 201]:
                test_battery_id = "TEST-FLOW-001"
                created_ids["battery_id"] = test_battery_id
                check("Created test battery", True)
            else:
                check("Create test battery", False, f"Status: {r2.status_code}")

    # 3e. Create battery rental with upfront payment
    if test_battery_id and cs_id:
        rental_data = {
            "user_id": test_user_id,
            "battery_ids": [str(test_battery_id)],
            "cost_structure_id": cs_id,
            "due_date": (datetime.now(timezone.utc) + timedelta(days=3)).isoformat(),
            "upfront_payment": {
                "payment_amount": 25.0,
                "payment_method": "cash"
            }
        }
        r = requests.post(f"{API_BASE_URL}/battery-rentals", json=rental_data, headers=headers(token))
        check("Create battery rental", r.status_code == 200, f"Status: {r.status_code}, Body: {r.text[:200]}")

        rental_id = None
        if r.status_code == 200:
            rental_response = r.json()
            rental_id = rental_response.get("rental_id")
            created_ids["rental_id"] = rental_id
            check("Rental ID assigned", bool(rental_id), f"rental_id={rental_id}")

            # Check upfront payment recorded
            upfront = rental_response.get("upfront_charges")
            check("Upfront charges recorded", upfront is not None, f"upfront_charges={upfront}")

            # Check deposit hold created
            deposit_hold = rental_response.get("deposit_hold")
            check("Deposit hold created", deposit_hold is not None, f"deposit_hold={deposit_hold}")

            # Verify credit summary shows held deposit
            r2 = requests.get(f"{API_BASE_URL}/accounts/user/{test_user_id}/credit-summary", headers=headers(token))
            if r2.status_code == 200:
                summary = r2.json()
                check("Deposit held in credit summary", summary.get("held_deposits", 0) > 0,
                      f"held_deposits={summary.get('held_deposits')}")
                check("Available credit reduced", summary.get("available_credit", 999) < summary.get("balance", 0),
                      f"available={summary.get('available_credit')}, balance={summary.get('balance')}")

            # Check deposit holds endpoint
            r3 = requests.get(f"{API_BASE_URL}/accounts/user/{test_user_id}/deposit-holds", headers=headers(token))
            check("Deposit holds endpoint", r3.status_code == 200)
            if r3.status_code == 200:
                holds = r3.json()
                check("Has active hold", len(holds) > 0, f"holds_count={len(holds)}")
                if holds:
                    check("Hold status is 'held'", holds[0].get("status") == "held")

        # 3f. Return battery (verify deposit released)
        if rental_id:
            r = requests.post(f"{API_BASE_URL}/battery-rentals/{rental_id}/return", json={
                "return_date": datetime.now(timezone.utc).isoformat()
            }, headers=headers(token))
            check("Return battery", r.status_code == 200, f"Status: {r.status_code}")

            # Verify deposit released
            r2 = requests.get(f"{API_BASE_URL}/accounts/user/{test_user_id}/deposit-holds",
                              params={"status": "held"}, headers=headers(token))
            if r2.status_code == 200:
                active_holds = r2.json()
                check("Deposit hold released", len(active_holds) == 0,
                      f"active_holds={len(active_holds)}")
    else:
        print("  SKIP  Skipping rental tests (no battery or cost structure)")


# ============================================================================
# 4. PUE Rental Lifecycle
# ============================================================================
section("4. PUE Rental Lifecycle")

if test_user_id and cs_id:
    # 4a. Get or create a PUE item
    r = requests.get(f"{API_BASE_URL}/hubs/{hub_id}/pue", headers=headers(token))
    test_pue_id = None
    if r.status_code == 200:
        pues = r.json()
        available = [p for p in pues if p.get("status") == "available"]
        if available:
            test_pue_id = available[0]["pue_id"]
            check("Found available PUE", True, f"pue_id={test_pue_id}")

    if not test_pue_id:
        r2 = requests.post(f"{API_BASE_URL}/pue/", json={
            "pue_id": "TEST-PUE-001",
            "hub_id": hub_id,
            "name": "Test PUE Item",
            "status": "available"
        }, headers=headers(token))
        if r2.status_code in [200, 201]:
            test_pue_id = "TEST-PUE-001"
            created_ids["pue_id"] = test_pue_id
            check("Created test PUE", True)

    # 4b. Create PUE cost structure (query params, components as JSON string)
    pue_cs_params = {
        "name": "Test PUE CS",
        "hub_id": hub_id,
        "item_type": "pue_item",
        "item_reference": test_pue_id or "all",
        "deposit_amount": 25.0,
        "components": json.dumps([
            {"component_name": "Daily Fee", "unit_type": "per_day", "rate": 5.0, "sort_order": 0}
        ])
    }
    r = requests.post(f"{API_BASE_URL}/settings/cost-structures", params=pue_cs_params, headers=headers(token))
    pue_cs_id = None
    if r.status_code in [200, 201]:
        pue_cs_id = r.json().get("structure_id") or r.json().get("cost_structure_id")
        created_ids["pue_cost_structure_id"] = pue_cs_id

    # 4c. Create PUE rental
    if test_pue_id and pue_cs_id:
        r = requests.post(f"{API_BASE_URL}/pue-rentals", json={
            "user_id": test_user_id,
            "pue_id": test_pue_id,
            "cost_structure_id": pue_cs_id,
            "deposit_amount": 25.0,
            "payment_type": "cash"
        }, headers=headers(token))
        check("Create PUE rental", r.status_code == 200, f"Status: {r.status_code}")

        pue_rental_id = None
        if r.status_code == 200:
            pue_rental_id = r.json().get("pue_rental_id")
            created_ids["pue_rental_id"] = pue_rental_id

            # Check deposit hold for PUE
            r2 = requests.get(f"{API_BASE_URL}/accounts/user/{test_user_id}/deposit-holds",
                              params={"status": "held"}, headers=headers(token))
            if r2.status_code == 200:
                holds = r2.json()
                pue_holds = [h for h in holds if h.get("rental_type") == "pue"]
                check("PUE deposit hold created", len(pue_holds) > 0, f"pue_holds={len(pue_holds)}")

        # 4d. Return PUE rental
        if pue_rental_id:
            r = requests.post(f"{API_BASE_URL}/pue-rentals/{pue_rental_id}/return", json={
                "actual_return_date": datetime.now(timezone.utc).isoformat()
            }, headers=headers(token))
            check("Return PUE rental", r.status_code == 200, f"Status: {r.status_code}")

            # Check deposit released
            r2 = requests.get(f"{API_BASE_URL}/accounts/user/{test_user_id}/deposit-holds",
                              params={"status": "held"}, headers=headers(token))
            if r2.status_code == 200:
                active_holds = r2.json()
                pue_active = [h for h in active_holds if h.get("rental_type") == "pue"]
                check("PUE deposit released", len(pue_active) == 0)


# ============================================================================
# 5. Deposit System - Insufficient Credit
# ============================================================================
section("5. Deposit System - Edge Cases")

if test_user_id and cs_id and test_battery_id:
    # 5a. Drain the account
    r = requests.get(f"{API_BASE_URL}/accounts/user/{test_user_id}", headers=headers(token))
    if r.status_code == 200:
        balance = r.json().get("balance", 0)
        if balance > 0:
            # Drain balance using adjustment with negative amount
            r2 = requests.post(f"{API_BASE_URL}/accounts/user/{test_user_id}/transaction", params={
                "amount": -balance,
                "transaction_type": "adjustment",
                "description": "Test: drain account"
            }, headers=headers(token))

    # Make battery available again (in case still rented)
    requests.put(f"{API_BASE_URL}/batteries/{test_battery_id}", json={"status": "available"}, headers=headers(token))

    # 5b. Try to rent with insufficient credit (should fail due to deposit hold)
    r = requests.post(f"{API_BASE_URL}/battery-rentals", json={
        "user_id": test_user_id,
        "battery_ids": [str(test_battery_id)],
        "cost_structure_id": cs_id,
        "due_date": (datetime.now(timezone.utc) + timedelta(days=1)).isoformat()
    }, headers=headers(token))
    check("Insufficient credit blocks rental", r.status_code == 400,
          f"Status: {r.status_code}, Body: {r.text[:200]}")
    if r.status_code == 400:
        check("Error mentions insufficient credit",
              "insufficient" in r.text.lower() or "credit" in r.text.lower(),
              f"Message: {r.text[:100]}")


# ============================================================================
# 6. Cost Structure with Decimal Durations
# ============================================================================
section("6. Decimal Duration Cost Structures")

decimal_cs_params = {
    "name": "Half-Month Test CS",
    "hub_id": hub_id,
    "item_type": "battery_capacity",
    "item_reference": "all",
    "deposit_amount": 0,
    "duration_options": json.dumps([
        {
            "input_type": "custom",
            "label": "Duration (months)",
            "default_value": 0.5,
            "min_value": 0.5,
            "max_value": 12.0,
            "custom_unit": "months"
        }
    ]),
    "components": json.dumps([
        {"component_name": "Monthly Rate", "unit_type": "per_month", "rate": 100.0, "sort_order": 0}
    ])
}

r = requests.post(f"{API_BASE_URL}/settings/cost-structures", params=decimal_cs_params, headers=headers(token))
check("Create decimal-duration cost structure", r.status_code in [200, 201], f"Status: {r.status_code}")

if r.status_code in [200, 201]:
    decimal_cs_id = r.json().get("structure_id") or r.json().get("cost_structure_id")
    created_ids["decimal_cost_structure_id"] = decimal_cs_id

    # Verify the duration options stored correctly
    r2 = requests.get(f"{API_BASE_URL}/settings/cost-structures/{decimal_cs_id}", headers=headers(token))
    if r2.status_code == 200:
        cs = r2.json()
        duration_opts = cs.get("duration_options", [])
        if duration_opts:
            opt = duration_opts[0]
            check("Decimal default_value stored", opt.get("default_value") == 0.5,
                  f"default_value={opt.get('default_value')}")
            check("Decimal min_value stored", opt.get("min_value") == 0.5,
                  f"min_value={opt.get('min_value')}")
            check("Decimal max_value stored", opt.get("max_value") == 12.0,
                  f"max_value={opt.get('max_value')}")
        else:
            check("Duration options returned", False, "No duration_options in response")


# ============================================================================
# 7. Cleanup
# ============================================================================
section("7. Cleanup")

cleanup_count = 0

# Clean up cost structures
for key in ["decimal_cost_structure_id", "pue_cost_structure_id", "cost_structure_id"]:
    if key in created_ids:
        r = requests.delete(f"{API_BASE_URL}/settings/cost-structures/{created_ids[key]}", headers=headers(token))
        if r.status_code == 200:
            cleanup_count += 1

# Clean up PUE
if "pue_id" in created_ids:
    r = requests.delete(f"{API_BASE_URL}/pue/{created_ids['pue_id']}", headers=headers(token))
    if r.status_code == 200:
        cleanup_count += 1

# Clean up battery
if "battery_id" in created_ids:
    r = requests.delete(f"{API_BASE_URL}/batteries/{created_ids['battery_id']}", headers=headers(token))
    if r.status_code == 200:
        cleanup_count += 1

# Clean up test user
if "user_id" in created_ids:
    r = requests.delete(f"{API_BASE_URL}/users/{created_ids['user_id']}", headers=headers(token))
    if r.status_code == 200:
        cleanup_count += 1

print(f"  Cleaned up {cleanup_count} test resources")


# ============================================================================
# Summary
# ============================================================================
print(f"\n{'='*60}")
print(f"  RESULTS: {passed} passed, {failed} failed ({passed + failed} total)")
print(f"{'='*60}")

if failed > 0:
    sys.exit(1)
