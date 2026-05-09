# tests/test_spending_overview.py

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

EXPECTED_CHART_TITLES = [
    "Spending by Category",
    "Daily Spending Over Time",
    "Monthly Income vs Expenses"
]


def test_spending_overview_charts_render(driver):
    """
    Verifies that all three Spending Overview charts render on page load.
    Confirms each chart is present in the DOM via stPlotlyChart elements
    and that each expected title appears in the page source SVG markup.

    Parameters:
        driver (webdriver.Chrome): Browser session injected by the driver fixture.

    Returns:
        None: Passes if all three charts render with correct titles.
              Raises AssertionError if chart count is wrong or a title is missing.
              Raises TimeoutException if charts never appear within 10 seconds.
    """
    driver.get("http://localhost:8501")

    wait = WebDriverWait(driver, 10)
    wait.until(
        EC.presence_of_element_located((By.CSS_SELECTOR, "[data-testid='stPlotlyChart']"))
    )

    # Confirm exactly 3 charts rendered
    charts = driver.find_elements(By.CSS_SELECTOR, "[data-testid='stPlotlyChart']")
    assert len(charts) == 3, f"Expected 3 charts but found {len(charts)}"

    # Confirm each chart title is present in the SVG page source
    page_source = driver.page_source
    for title in EXPECTED_CHART_TITLES:
        assert title in page_source, f"Chart title '{title}' not found in page source"