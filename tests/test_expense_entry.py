# tests/test_expense_entry.py

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.keys import Keys

TEST_ITEM = "Selenium Test Coffee"
TEST_AMOUNT = "4.50"

def test_expense_entry():
    """
    Interaction test — verifies that submitting the Add Expense form
    saves a new transaction and displays it in the transaction history table.
    Enters a known item name and amount, clicks Add Expense, then confirms
    the item appears in the rendered dataframe.

    Parameters:
        None

    Returns:
        None: Passes if the test item appears in the table after submission.
              Raises AssertionError if the item is not found.
              Raises TimeoutException if the table never renders within 10 seconds.
    """
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()))

    try:
        driver.get("http://localhost:8501")

        # Wait for the Expense Name input to confirm the page is fully rendered
        wait = WebDriverWait(driver, 10)
        name_field = wait.until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "[aria-label='Expense Name']"))
        )

        # Locate the Amount field
        amount_field = driver.find_element(By.CSS_SELECTOR, "[data-testid='stNumberInputField']")

        # Type into both fields
        name_field.clear()
        name_field.send_keys(TEST_ITEM)
        amount_field.send_keys(Keys.CONTROL + "a")
        amount_field.send_keys(TEST_AMOUNT)

        # Find the correct button — there are multiple secondary buttons on the page
        # so we filter by visible text content to target Add Expense specifically
        buttons = driver.find_elements(By.CSS_SELECTOR, "[data-testid='stBaseButton-secondary']")
        add_button = next(btn for btn in buttons if "Add Expense" in btn.text)
        add_button.click()

        # Wait for the table to re-render after form submission
        wait.until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "[data-testid='stDataFrameResizable']"))
        )

        # Canvas-based tables return empty .text — assert against page source instead
        # Streamlit embeds cell data in the DOM even when rendered on canvas
        page_source = driver.page_source
        assert TEST_ITEM in page_source, f"Expected '{TEST_ITEM}' in page source but it was not found."

    finally:
        driver.quit()