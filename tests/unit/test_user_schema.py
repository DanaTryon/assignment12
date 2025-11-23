import pytest
from uuid import uuid4
from datetime import datetime
from app.schemas import user as user_schemas

# -------------------------------
# UserCreate
# -------------------------------

def test_user_create_valid():
    schema = user_schemas.UserCreate(
        first_name="John",
        last_name="Doe",
        email="john@example.com",
        username="johndoe",
        password="StrongPass1!",
        confirm_password="StrongPass1!"
    )
    assert schema.password == "StrongPass1!"

def test_user_create_password_mismatch():
    with pytest.raises(ValueError) as exc_info:
        user_schemas.UserCreate(
            first_name="John",
            last_name="Doe",
            email="john@example.com",
            username="johndoe",
            password="StrongPass1!",
            confirm_password="WrongPass1!"
        )
    assert "Passwords do not match" in str(exc_info.value)

@pytest.mark.parametrize("password,error", [
    ("alllowercase1!", "Password must contain at least one uppercase letter"),
    ("ALLUPPERCASE1!", "Password must contain at least one lowercase letter"),
    ("NoDigits!", "Password must contain at least one digit"),
    ("NoSpecial1", "Password must contain at least one special character"),
])
def test_user_create_password_strength(password, error):
    with pytest.raises(ValueError) as exc_info:
        user_schemas.UserCreate(
            first_name="John",
            last_name="Doe",
            email="john@example.com",
            username="johndoe",
            password=password,
            confirm_password=password
        )
    assert error in str(exc_info.value)

# -------------------------------
# UserResponse
# -------------------------------

def test_user_response_valid():
    schema = user_schemas.UserResponse(
        id=uuid4(),
        username="johndoe",
        email="john@example.com",
        first_name="John",
        last_name="Doe",
        is_active=True,
        is_verified=False,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    assert schema.username == "johndoe"
    assert schema.is_active is True

# -------------------------------
# UserLogin
# -------------------------------

def test_user_login_valid():
    schema = user_schemas.UserLogin(
        username="johndoe",
        password="SecurePass123!"
    )
    assert schema.username == "johndoe"

# -------------------------------
# UserUpdate
# -------------------------------

def test_user_update_partial():
    schema = user_schemas.UserUpdate(first_name="Jane")
    assert schema.first_name == "Jane"
    assert schema.last_name is None
    assert schema.email is None
    assert schema.username is None

# -------------------------------
# PasswordUpdate
# -------------------------------

def test_password_update_valid():
    schema = user_schemas.PasswordUpdate(
        current_password="OldPass123!",
        new_password="NewPass123!",
        confirm_new_password="NewPass123!"
    )
    assert schema.new_password == "NewPass123!"

def test_password_update_mismatch():
    with pytest.raises(ValueError) as exc_info:
        user_schemas.PasswordUpdate(
            current_password="OldPass123!",
            new_password="NewPass123!",
            confirm_new_password="WrongPass123!"
        )
    assert "New password and confirmation do not match" in str(exc_info.value)

def test_password_update_same_as_current():
    with pytest.raises(ValueError) as exc_info:
        user_schemas.PasswordUpdate(
            current_password="SamePass123!",
            new_password="SamePass123!",
            confirm_new_password="SamePass123!"
        )
    assert "New password must be different from current password" in str(exc_info.value)

