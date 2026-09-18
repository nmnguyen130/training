import asyncio
import json
import sys
import urllib.error
import urllib.parse
import urllib.request
from sqlalchemy import select

from app.core.database import app_engine, app_session
from app.modules.auth.model import UserAccount
from app.modules.rbac.model import UserRole

BASE_URL = "http://localhost:8000/api/v1"


def request(method: str, path: str, data: dict = None, token: str = None) -> tuple[int, dict | list]:
    url = f"{BASE_URL}{path}"
    headers = {"Content-Type": "application/json", "Accept": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"

    body = json.dumps(data).encode("utf-8") if data is not None else None
    req = urllib.request.Request(url, data=body, headers=headers, method=method)

    try:
        with urllib.request.urlopen(req) as resp:
            status_code = resp.status
            resp_body = resp.read().decode("utf-8")
            return status_code, json.loads(resp_body) if resp_body else {}
    except urllib.error.HTTPError as e:
        resp_body = e.read().decode("utf-8")
        try:
            return e.code, json.loads(resp_body)
        except Exception:
            return e.code, {"error": resp_body}


async def assign_super_admin(username: str):
    async with app_session() as session:
        user = await session.scalar(select(UserAccount).where(UserAccount.username == username))
        if not user:
            raise RuntimeError(f"User {username} not found")
        existing = await session.scalar(
            select(UserRole).where(UserRole.user_id == user.user_id, UserRole.role_id == 1)
        )
        if not existing:
            session.add(UserRole(user_id=user.user_id, role_id=1))
            await session.commit()
    await app_engine.dispose()


def run_tests():
    print("=" * 60)
    print("STARTING RBAC API TESTS USING URLLIB")
    print("=" * 60)

    # 1. Setup Auth & Super Admin
    username = "admin_tester"
    password = "password123"

    print("\n[1. AUTH & SETUP]")
    reg_status, reg_data = request("POST", "/auth/register", {
        "username": username,
        "password": password,
        "display_name": "Admin Tester",
        "email": "admin@example.com",
    })

    if reg_status in (201, 409):
        print(f"  ✓ User ready ({username})")
    else:
        print(f"  ✗ Register error: {reg_status} {reg_data}")
        sys.exit(1)

    asyncio.run(assign_super_admin(username))
    print(f"  ✓ Assigned super_admin role to {username}")

    login_status, login_data = request("POST", "/auth/login", {"username": username, "password": password})
    assert login_status == 200, f"Login failed: {login_data}"
    token = login_data["access_token"]
    print(f"  ✓ Logged in. Bearer token obtained.")

    me_status, me_data = request("GET", "/users/me", token=token)
    user_id = me_data["user_id"]

    total_passed = 0
    total_tests = 0

    def test(name: str, method: str, path: str, data: dict = None, expected_status: int = 200):
        nonlocal total_passed, total_tests
        total_tests += 1
        status_code, resp = request(method, path, data, token)
        passed = status_code == expected_status
        if passed:
            total_passed += 1
            print(f"  ✓ [{method}] {path} -> {status_code} OK")
        else:
            print(f"  ✗ [{method}] {path} -> Expected {expected_status}, got {status_code}: {resp}")
        return status_code, resp

    # 2. Roles Endpoints
    print("\n[2. TESTING ROLES API]")
    _, roles_page = test("List Roles", "GET", "/roles", expected_status=200)
    assert len(roles_page.get("items", [])) >= 4, "Missing seeded roles!"
    print(f"    Total roles in database: {roles_page['total']}")

    _, search_roles = test("Search Roles", "GET", "/roles?search=warehouse", expected_status=200)
    assert search_roles["total"] >= 2, "Search roles failed!"

    create_role_payload = {
        "role_code": "qc_inspector",
        "role_name": "QC Inspector",
        "description": "Quality Control Inspector",
        "permission_ids": [11, 13],  # product.read, inventory.read
    }
    _, new_role = test("Create Role", "POST", "/roles", data=create_role_payload, expected_status=201)
    new_role_id = new_role["role_id"]
    assert new_role["role_code"] == "qc_inspector"
    assert len(new_role["permissions"]) == 2
    print(f"    Created role ID {new_role_id} with {len(new_role['permissions'])} permissions.")

    _, get_role_resp = test("Get Role Details", "GET", f"/roles/{new_role_id}", expected_status=200)
    assert get_role_resp["role_id"] == new_role_id
    assert len(get_role_resp["permissions"]) == 2

    update_role_payload = {"role_name": "Senior QC Inspector", "description": "Lead Quality Control Inspector"}
    _, updated_role = test("Update Role", "PATCH", f"/roles/{new_role_id}", data=update_role_payload, expected_status=200)
    assert updated_role["role_name"] == "Senior QC Inspector"

    set_perms_payload = {"permission_ids": [11, 13, 14]}  # product.read, inventory.read, inventory.manage
    _, perm_updated_role = test("Set Role Permissions", "PUT", f"/roles/{new_role_id}/permissions", data=set_perms_payload, expected_status=200)
    assert len(perm_updated_role["permissions"]) == 3

    test("Delete Custom Role", "DELETE", f"/roles/{new_role_id}", expected_status=204)
    test("Verify Role Deleted", "GET", f"/roles/{new_role_id}", expected_status=404)

    # 3. Permissions Endpoints
    print("\n[3. TESTING PERMISSIONS API]")
    _, perms_page = test("List Permissions", "GET", "/permissions", expected_status=200)
    assert perms_page["total"] >= 16, "Missing permissions!"
    print(f"    Total permissions in database: {perms_page['total']}")

    _, search_perms = test("Search Permissions", "GET", "/permissions?search=inbound", expected_status=200)
    assert search_perms["total"] >= 1, "Search permissions failed!"

    create_perm_payload = {
        "permission_code": "quality.inspect",
        "description": "Perform quality inspection checks",
    }
    _, new_perm = test("Create Permission", "POST", "/permissions", data=create_perm_payload, expected_status=201)
    new_perm_id = new_perm["permission_id"]
    assert new_perm["permission_code"] == "quality.inspect"

    _, get_perm_resp = test("Get Permission", "GET", f"/permissions/{new_perm_id}", expected_status=200)
    assert get_perm_resp["permission_code"] == "quality.inspect"

    update_perm_payload = {"description": "Updated quality inspection description", "is_active": True}
    _, updated_perm = test("Update Permission", "PATCH", f"/permissions/{new_perm_id}", data=update_perm_payload, expected_status=200)
    assert updated_perm["description"] == "Updated quality inspection description"

    # 4. User Roles Endpoints
    print("\n[4. TESTING USER ROLES API]")
    _, user_roles = test("Get User Roles", "GET", f"/users/{user_id}/roles", expected_status=200)
    print(f"    User has assigned roles: {[r['role']['role_code'] for r in user_roles]}")

    assign_payload = {"role_ids": [1, 2]}  # super_admin + warehouse_manager
    _, assigned_roles = test("Assign User Roles", "PUT", f"/users/{user_id}/roles", data=assign_payload, expected_status=200)
    assert len(assigned_roles) == 2
    assigned_codes = {r["role"]["role_code"] for r in assigned_roles}
    assert "super_admin" in assigned_codes and "warehouse_manager" in assigned_codes
    print(f"    Assigned roles verified: {assigned_codes}")

    print("\n" + "=" * 60)
    print(f"SUMMARY: {total_passed}/{total_tests} RBAC API TESTS PASSED SUCCESSFULLY!")
    print("=" * 60)


if __name__ == "__main__":
    run_tests()
