import os

import pytest


@pytest.fixture(scope="session")
def appify_creds() -> dict[str, str]:
    business = os.getenv("APPIFY_TEST_BUSINESS_NAME")
    email = os.getenv("APPIFY_TEST_EMAIL")
    password = os.getenv("APPIFY_TEST_PASSWORD")
    if not all([business, email, password]):
        pytest.skip("Set APPIFY_TEST_BUSINESS_NAME / EMAIL / PASSWORD to run upstream tests")
    return {"business_name": business, "email": email, "password": password}
