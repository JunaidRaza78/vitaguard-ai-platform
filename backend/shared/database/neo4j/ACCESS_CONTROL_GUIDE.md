# Access Control Guide - Neo4j Family Health Manager

## Overview

Complete access control system for securing family health data with role-based permissions and guardian relationships.

---

## 🔐 Key Concepts

### 1. **Family Roles**
- **admin** - Full control over family and all members
- **parent** - Can add/remove members, view all family data
- **child** - Limited to own data
- **member** - Standard family member access

### 2. **Guardian Relationships**
- **GUARDIAN_OF** - Full access to ward's health data
- Types: `parent`, `legal_guardian`, `caretaker`
- Grants both view and modify permissions

### 3. **Permission Levels**
- **View** - Can see health data
- **Modify** - Can edit health data
- **Add Members** - Can add new family members
- **Remove Members** - Can remove family members

---

## 🚀 Quick Start Examples

### Example 1: Add Family Member with Permission Check

```python
from backend.shared.database.neo4j import Neo4jClient

client = Neo4jClient()

# User trying to add a new member
requesting_user_id = "user-001"  # Must be admin/parent/creator
new_member_id = "user-002"
family_id = "family-001"

# Secure add with automatic permission check
result = client.add_family_member_secure(
    requesting_user_id=requesting_user_id,
    new_member_user_id=new_member_id,
    family_id=family_id,
    role="child"
)

if result["success"]:
    print(f"✅ {result['message']}")
    print(f"Relationship: {result['relationship']}")
else:
    print(f"❌ {result['message']}")
```

**Output if successful:**
```
✅ Member added successfully as child
Relationship: {'role': 'child', 'joinedAt': '2024-01-15T10:00:00', 'addedBy': 'user-001'}
```

**Output if permission denied:**
```
❌ Permission denied: User role 'child' does not have permission to add members
```

---

### Example 2: Check if User Can View Another Member's Data

```python
# Check viewing permission
requesting_user_id = "parent-001"
target_user_id = "child-001"

permission = client.user_can_view_member_data(
    requesting_user_id=requesting_user_id,
    target_user_id=target_user_id
)

if permission["has_permission"]:
    print(f"✅ Access granted: {permission['reason']}")
    print(f"Relationship: {permission['relationship']}")

    # Now fetch the data
    health_records = client.get_user_health_records(target_user_id)
    conditions = client.get_user_conditions(target_user_id)
else:
    print(f"❌ Access denied: {permission['reason']}")
```

---

### Example 3: Create Guardian Relationship

```python
# Parent becomes guardian of child
guardian_id = "parent-001"
child_id = "child-001"

success = client.create_guardian_relationship(
    guardian_user_id=guardian_id,
    ward_user_id=child_id,
    relationship_type="parent"
)

if success:
    print("✅ Guardian relationship created")

    # Guardian can now access child's data
    permission = client.user_can_modify_member_data(guardian_id, child_id)
    print(f"Can modify data: {permission['has_permission']}")
else:
    print("❌ Failed to create guardian relationship")
```

---

### Example 4: Remove Family Member with Permission Check

```python
requesting_user_id = "admin-001"
member_to_remove = "member-001"
family_id = "family-001"

result = client.remove_family_member_secure(
    requesting_user_id=requesting_user_id,
    member_user_id=member_to_remove,
    family_id=family_id
)

print(result["message"])
# Output: "Member removed successfully"
# OR: "Permission denied: User role 'member' does not have permission to add members"
```

---

### Example 5: Update Member Role

```python
# Admin updating member's role
requesting_user_id = "admin-001"
target_user_id = "member-001"
family_id = "family-001"

result = client.update_family_member_role(
    requesting_user_id=requesting_user_id,
    target_user_id=target_user_id,
    family_id=family_id,
    new_role="parent"
)

if result["success"]:
    print(f"✅ {result['message']}")
else:
    print(f"❌ {result['message']}")
```

---

## 📊 Permission Matrix

| Action | Self | Guardian | Family Admin | Family Parent | Family Child | Non-Member |
|--------|------|----------|--------------|---------------|--------------|------------|
| **View own data** | ✅ | ✅ | ✅ | ✅ | ✅ | ❌ |
| **Modify own data** | ✅ | ✅ | ✅ | ✅ | ✅ | ❌ |
| **View family member data** | ✅ | ✅ | ✅ | ✅ | ❌ | ❌ |
| **Modify family member data** | ✅ | ✅ (ward only) | ✅ | ❌ | ❌ | ❌ |
| **Add family members** | - | - | ✅ | ✅ | ❌ | ❌ |
| **Remove family members** | - | - | ✅ | ✅ | ❌ | ❌ |
| **Change member roles** | - | - | ✅ | ❌ | ❌ | ❌ |

---

## 🔍 Permission Check Functions

### 1. Check Add Member Permission

```python
permission = client.user_can_add_family_member(
    user_id="user-001",
    family_id="family-001"
)

# Returns:
{
    "has_permission": True/False,
    "reason": "User is family creator" | "User has admin role" | ...,
    "user_role": "admin" | "parent" | "child" | None
}
```

**Who can add members:**
- ✅ Family creator (createdBy)
- ✅ Family admin
- ✅ Family parent
- ❌ Family child
- ❌ Non-member

---

### 2. Check View Data Permission

```python
permission = client.user_can_view_member_data(
    requesting_user_id="user-001",
    target_user_id="user-002"
)

# Returns:
{
    "has_permission": True/False,
    "reason": "Own data" | "Same family, requestor role: admin" | ...,
    "relationship": "self" | "guardian" | "family" | None
}
```

**Who can view:**
- ✅ Self (own data)
- ✅ Guardian (ward's data)
- ✅ Family admin (all family member data)
- ✅ Family parent (all family member data)
- ❌ Family child (only own data)
- ❌ Non-member

---

### 3. Check Modify Data Permission

```python
permission = client.user_can_modify_member_data(
    requesting_user_id="user-001",
    target_user_id="user-002"
)

# Returns:
{
    "has_permission": True/False,
    "reason": "Own data" | "User is guardian" | "User is family admin"
}
```

**Who can modify:**
- ✅ Self (own data)
- ✅ Guardian (ward's data only)
- ✅ Family admin (all family member data)
- ❌ Family parent (cannot modify other members' data)
- ❌ Non-member

---

## 🔗 Guardian Relationships

### Create Guardian

```python
success = client.create_guardian_relationship(
    guardian_user_id="parent-001",
    ward_user_id="child-001",
    relationship_type="parent"  # or "legal_guardian", "caretaker"
)
```

### Get User's Guardians

```python
guardians = client.get_user_guardians(user_id="child-001")

# Returns:
[
    {
        "guardian": {
            "userId": "parent-001",
            "name": "John Doe",
            ...
        },
        "relationship": {
            "relationshipType": "parent",
            "createdAt": "2024-01-15T10:00:00",
            "canViewData": True,
            "canModifyData": True
        }
    }
]
```

### Get User's Wards

```python
wards = client.get_user_wards(guardian_user_id="parent-001")

# Returns list of people under guardianship
```

---

## 📝 Audit Trail

### Log Access Attempts

```python
client.log_access_attempt(
    user_id="user-001",
    action="view",
    resource_type="HealthRecord",
    resource_id="record-123",
    granted=True,
    reason="User is guardian"
)
```

### Get Access Logs

```python
# Get all logs
all_logs = client.get_access_logs(limit=100)

# Get logs for specific user
user_logs = client.get_access_logs(user_id="user-001", limit=50)

# Returns:
[
    {
        "logId": "log-001",
        "userId": "user-001",
        "action": "view",
        "resourceType": "HealthRecord",
        "resourceId": "record-123",
        "granted": True,
        "reason": "User is guardian",
        "timestamp": "2024-01-15T10:30:00"
    }
]
```

---

## 🎯 Complete Workflow Example

```python
from backend.shared.database.neo4j import Neo4jClient

client = Neo4jClient()

# 1. Create family
family = client.create_family(
    name="Doe Family",
    created_by="parent-001"
)

# 2. Parent automatically becomes admin (creator)
# Add child to family (parent has permission as creator)
result = client.add_family_member_secure(
    requesting_user_id="parent-001",
    new_member_user_id="child-001",
    family_id=family["familyId"],
    role="child"
)

# 3. Create guardian relationship
client.create_guardian_relationship(
    guardian_user_id="parent-001",
    ward_user_id="child-001",
    relationship_type="parent"
)

# 4. Parent can now access child's health data
permission = client.user_can_view_member_data("parent-001", "child-001")
if permission["has_permission"]:
    # Get child's health records
    records = client.get_user_health_records("child-001")
    conditions = client.get_user_conditions("child-001")
    medications = client.get_user_medications("child-001")

    # Log the access
    client.log_access_attempt(
        user_id="parent-001",
        action="view",
        resource_type="HealthRecord",
        resource_id="child-001",
        granted=True,
        reason=permission["reason"]
    )

# 5. Try to add another member as child (should fail)
result = client.add_family_member_secure(
    requesting_user_id="child-001",  # Child trying to add
    new_member_user_id="uncle-001",
    family_id=family["familyId"],
    role="member"
)
# Output: Permission denied: User role 'child' does not have permission to add members
```

---

## 🔒 Security Best Practices

### 1. Always Check Permissions Before Operations

```python
# ❌ BAD - Direct access without check
records = client.get_user_health_records(target_user_id)

# ✅ GOOD - Check permission first
permission = client.user_can_view_member_data(requesting_user_id, target_user_id)
if permission["has_permission"]:
    records = client.get_user_health_records(target_user_id)
else:
    raise PermissionError(permission["reason"])
```

### 2. Use Secure Operations

```python
# ✅ Use secure operations that include permission checks
result = client.add_family_member_secure(...)
result = client.remove_family_member_secure(...)
result = client.update_family_member_role(...)
```

### 3. Log Important Actions

```python
# Log all data access
client.log_access_attempt(
    user_id=requesting_user_id,
    action="modify",
    resource_type="Medication",
    resource_id=medication_id,
    granted=has_permission,
    reason=permission_reason
)
```

### 4. Validate Roles

```python
# Ensure valid roles
VALID_ROLES = ["admin", "parent", "child", "member"]
if role not in VALID_ROLES:
    raise ValueError(f"Invalid role: {role}")
```

---

## 🧪 Testing Access Control

```python
def test_access_control():
    client = Neo4jClient()

    # Test 1: Family creator can add members
    permission = client.user_can_add_family_member("creator-001", "family-001")
    assert permission["has_permission"] == True

    # Test 2: Child cannot add members
    permission = client.user_can_add_family_member("child-001", "family-001")
    assert permission["has_permission"] == False

    # Test 3: Guardian can view ward data
    permission = client.user_can_view_member_data("parent-001", "child-001")
    assert permission["has_permission"] == True
    assert permission["relationship"] == "guardian"

    # Test 4: Non-member cannot view data
    permission = client.user_can_view_member_data("stranger-001", "child-001")
    assert permission["has_permission"] == False

    print("✅ All access control tests passed!")
```

---

## 📚 API Reference Summary

| Function | Purpose | Required Permission |
|----------|---------|---------------------|
| `user_can_add_family_member()` | Check add permission | - |
| `user_can_view_member_data()` | Check view permission | - |
| `user_can_modify_member_data()` | Check modify permission | - |
| `add_family_member_secure()` | Add member with check | Admin/Parent/Creator |
| `remove_family_member_secure()` | Remove member with check | Admin/Parent/Creator |
| `update_family_member_role()` | Change member role | Admin/Creator |
| `create_guardian_relationship()` | Create guardian link | - |
| `get_user_guardians()` | Get guardians | - |
| `get_user_wards()` | Get wards | - |
| `log_access_attempt()` | Log access | - |
| `get_access_logs()` | Get logs | - |

---

## 🎯 Summary

Ab aapki family health management system me **complete access control** hai:

✅ **Role-based permissions** (admin, parent, child, member)
✅ **Guardian relationships** (parent-child, legal guardian)
✅ **Secure operations** (automatic permission checks)
✅ **Audit trail** (access logging)
✅ **Granular control** (view vs modify permissions)

**Key Takeaway:** Sirf authorized users hi family members ko add/remove kar sakte hain! 🔒
