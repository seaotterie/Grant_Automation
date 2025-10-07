"""
Modal System Integration Tests
Tests the complete modal framework including:
- Modal component loading
- Data files (NTEE codes, Government criteria)
- Template loading
- Modal open/close functionality
- Keyboard shortcuts
- Form interactions

Status: ACTIVE - Phase 9 Week 4 Modal Testing
"""

import time
import pytest
from playwright.sync_api import Page, expect

BASE_URL = "http://localhost:8000"
TEST_PAGE_URL = f"{BASE_URL}/test_modal_loading.html"


class TestModalSystemInfrastructure:
    """Test Phase 1: Basic Modal Infrastructure"""

    def test_01_test_page_loads(self, page: Page):
        """Test 1: Modal test page loads successfully"""
        page.goto(TEST_PAGE_URL)
        expect(page.locator("h1")).to_contain_text("Modal System Test")
        print("[OK] Test page loaded")

    def test_02_alpine_js_loads(self, page: Page):
        """Test 2: Alpine.js loads successfully"""
        page.goto(TEST_PAGE_URL)
        time.sleep(2)  # Wait for status checks

        alpine_status = page.locator("#alpine-status")
        expect(alpine_status).to_contain_text("Alpine.js loaded")
        print("[OK] Alpine.js loaded")

    def test_03_ntee_codes_load(self, page: Page):
        """Test 3: NTEE codes data loads"""
        page.goto(TEST_PAGE_URL)
        time.sleep(2)

        ntee_status = page.locator("#ntee-status")
        expect(ntee_status).to_contain_text("NTEE codes loaded")
        expect(ntee_status).to_contain_text("categories")
        print("[OK] NTEE codes loaded")

    def test_04_government_criteria_loads(self, page: Page):
        """Test 4: Government criteria data loads"""
        page.goto(TEST_PAGE_URL)
        time.sleep(2)

        criteria_status = page.locator("#criteria-status")
        expect(criteria_status).to_contain_text("Government criteria loaded")
        expect(criteria_status).to_contain_text("categories")
        print("[OK] Government criteria loaded")

    def test_05_modal_component_loads(self, page: Page):
        """Test 5: Modal component JavaScript loads"""
        page.goto(TEST_PAGE_URL)
        time.sleep(2)

        component_status = page.locator("#modal-component-status")
        expect(component_status).to_contain_text("Modal component loaded")
        print("[OK] Modal component loaded")

    def test_06_modal_templates_load(self, page: Page):
        """Test 6: Modal templates load into DOM"""
        page.goto(TEST_PAGE_URL)
        time.sleep(3)  # Extra time for async template loading

        templates_status = page.locator("#modal-templates-status")
        expect(templates_status).to_contain_text("Modal templates loaded")
        print("[OK] Modal templates loaded")


class TestModalFunctionality:
    """Test Phase 2: Modal Open/Close Functionality"""

    def test_07_create_profile_modal_opens(self, page: Page):
        """Test 7: Create Profile modal opens via button click"""
        page.goto(TEST_PAGE_URL)
        time.sleep(3)  # Wait for templates to load

        # Click the "Open Create Profile Modal" button
        create_button = page.locator("text=Open Create Profile Modal")
        create_button.click()

        time.sleep(1)  # Wait for modal to open

        # Check if modal is visible
        modal = page.locator("#create-profile-modal-container")
        expect(modal).to_be_visible()
        print("[OK] Create Profile modal opens")

    def test_08_create_profile_modal_closes(self, page: Page):
        """Test 8: Create Profile modal closes"""
        page.goto(TEST_PAGE_URL)
        time.sleep(3)

        # Open modal
        page.locator("text=Open Create Profile Modal").click()
        time.sleep(1)

        # Close modal (try clicking backdrop or close button)
        close_button = page.locator("#create-profile-modal-container button[aria-label='Close']")
        if close_button.is_visible():
            close_button.click()
        else:
            # Try ESC key
            page.keyboard.press("Escape")

        time.sleep(1)

        # Check if modal is hidden
        modal = page.locator("#create-profile-modal-container")
        expect(modal).not_to_be_visible()
        print("[OK] Create Profile modal closes")

    def test_09_edit_profile_modal_opens(self, page: Page):
        """Test 9: Edit Profile modal opens via button click"""
        page.goto(TEST_PAGE_URL)
        time.sleep(3)

        # Click the "Open Edit Profile Modal" button
        edit_button = page.locator("text=Open Edit Profile Modal")
        edit_button.click()

        time.sleep(1)

        # Check if modal is visible
        modal = page.locator("#edit-profile-modal-container")
        expect(modal).to_be_visible()
        print("[OK] Edit Profile modal opens")

    def test_10_keyboard_shortcut_esc_closes(self, page: Page):
        """Test 10: ESC key closes modal"""
        page.goto(TEST_PAGE_URL)
        time.sleep(3)

        # Open modal
        page.locator("text=Open Create Profile Modal").click()
        time.sleep(1)

        # Press ESC
        page.keyboard.press("Escape")
        time.sleep(1)

        # Check if modal is hidden
        modal = page.locator("#create-profile-modal-container")
        expect(modal).not_to_be_visible()
        print("[OK] ESC key closes modal")


class TestModalData:
    """Test Phase 3: Modal Data Integration"""

    def test_11_ntee_data_accessible(self, page: Page):
        """Test 11: NTEE codes data is accessible in JavaScript"""
        page.goto(TEST_PAGE_URL)
        time.sleep(2)

        # Check JavaScript global
        ntee_count = page.evaluate("Object.keys(NTEE_CODES || {}).length")
        assert ntee_count > 0, "NTEE_CODES should have categories"
        assert ntee_count >= 26, f"Expected at least 26 NTEE categories, got {ntee_count}"
        print(f"[OK] NTEE codes accessible ({ntee_count} categories)")

    def test_12_government_criteria_accessible(self, page: Page):
        """Test 12: Government criteria data is accessible in JavaScript"""
        page.goto(TEST_PAGE_URL)
        time.sleep(2)

        # Check JavaScript global
        criteria_count = page.evaluate("(GOVERNMENT_CRITERIA || []).length")
        assert criteria_count > 0, "GOVERNMENT_CRITERIA should have categories"
        assert criteria_count >= 6, f"Expected at least 6 criteria categories, got {criteria_count}"
        print(f"[OK] Government criteria accessible ({criteria_count} categories)")

    def test_13_modal_component_function_exists(self, page: Page):
        """Test 13: Modal component function exists"""
        page.goto(TEST_PAGE_URL)
        time.sleep(2)

        # Check if modalComponent function exists
        has_modal_component = page.evaluate("typeof modalComponent === 'function'")
        assert has_modal_component, "modalComponent function should exist"
        print("[OK] Modal component function exists")


class TestMainAppIntegration:
    """Test Phase 4: Main App Integration"""

    def test_14_main_app_loads_modal_system(self, page: Page):
        """Test 14: Main app loads modal system scripts"""
        page.goto(BASE_URL)
        time.sleep(3)

        # Check if scripts are loaded by looking for global variables
        has_ntee = page.evaluate("typeof NTEE_CODES !== 'undefined'")
        has_criteria = page.evaluate("typeof GOVERNMENT_CRITERIA !== 'undefined'")
        has_modal = page.evaluate("typeof modalComponent !== 'undefined'")

        assert has_ntee, "Main app should load NTEE codes"
        assert has_criteria, "Main app should load Government criteria"
        assert has_modal, "Main app should load modal component"
        print("[OK] Main app loads modal system")

    def test_15_main_app_has_modal_templates(self, page: Page):
        """Test 15: Main app has modal templates in DOM"""
        page.goto(BASE_URL)
        time.sleep(4)  # Extra time for template loading

        # Check for modal containers
        has_create_modal = page.locator("#create-profile-modal-container").count() > 0
        has_edit_modal = page.locator("#edit-profile-modal-container").count() > 0

        assert has_create_modal, "Main app should have create profile modal"
        assert has_edit_modal, "Main app should have edit profile modal"
        print("[OK] Main app has modal templates")


@pytest.fixture
def page(browser):
    """Create a new page for each test"""
    page = browser.new_page()
    yield page
    page.close()


@pytest.fixture(scope="session")
def browser():
    """Create browser instance for all tests"""
    from playwright.sync_api import sync_playwright

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        yield browser
        browser.close()


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v", "-s"])
