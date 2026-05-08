# Lightweight Flask server that handles Plaid Link authentication flow.
# Runs alongside Streamlit to handle the JavaScript-based Plaid Link widget.
# 
# Flow:
#   1. Streamlit opens this server's /plaid page in a new browser tab
#   2. User logs into their bank through Plaid Link
#   3. Plaid returns a public_token, Flask exchanges it for an access_token
#   4. access_token saved to plaid_token.txt for Streamlit to read
#
# Run with: python plaid_link/server.py

from flask import Flask, request, jsonify, render_template_string
import plaid
from plaid.api import plaid_api
from plaid.model.link_token_create_request import LinkTokenCreateRequest
from plaid.model.link_token_create_request_user import LinkTokenCreateRequestUser
from plaid.model.item_public_token_exchange_request import ItemPublicTokenExchangeRequest
from plaid.model.products import Products
from plaid.model.country_code import CountryCode
from dotenv import load_dotenv
from pathlib import Path
import os

# Load .env from project root
load_dotenv(dotenv_path=Path(__file__).parent.parent / ".env")

app = Flask(__name__)

# --- Plaid client setup ---
# Using sandbox environment for development/testing
# Switch to plaid.Environment.Production when ready for real bank data
configuration = plaid.Configuration(
    host=plaid.Environment.Sandbox,
    api_key={
        "clientId": os.getenv("PLAID_CLIENT_ID"),
        "secret": os.getenv("PLAID_SANDBOX_SECRET"),
    }
)

api_client = plaid.ApiClient(configuration)
client = plaid_api.PlaidApi(api_client)

# Path where access token is saved so Streamlit can read it
TOKEN_PATH = Path(__file__).parent.parent / "plaid_token.txt"

# --- HTML page that runs Plaid Link in the browser ---
# This is a minimal HTML page with embedded JavaScript
# Plaid Link is a JavaScript widget — this is why we need Flask
LINK_PAGE = """
<!DOCTYPE html>
<html>
<head><title>Connect Your Bank</title></head>
<body>
    <h2>Connecting your bank account...</h2>
    <p>A window should appear. If not, <a href="#" onclick="launchLink()">click here</a>.</p>

    <script src="https://cdn.plaid.com/link/v2/stable/link-initialize.js"></script>
    <script>
        async function launchLink() {
            // Fetch the link token from our Flask server
            const res = await fetch('/create_link_token');
            const data = await res.json();

            const handler = Plaid.create({
                token: data.link_token,
                onSuccess: async (public_token, metadata) => {
                    // Send public token back to Flask to exchange for access token
                    await fetch('/exchange_token', {
                        method: 'POST',
                        headers: {'Content-Type': 'application/json'},
                        body: JSON.stringify({public_token: public_token})
                    });
                    document.body.innerHTML = '<h2>✅ Bank connected successfully! You can close this tab.</h2>';
                },
                onExit: (err) => {
                    if (err) document.body.innerHTML = '<h2>❌ Connection failed. Please try again.</h2>';
                }
            });
            handler.open();
        }
        // Auto-launch on page load
        window.onload = launchLink;
    </script>
</body>
</html>
"""

@app.route("/plaid")
def plaid_page():
    """Serves the HTML page that launches Plaid Link in the browser."""
    return render_template_string(LINK_PAGE)


@app.route("/create_link_token")
def create_link_token():
    """
    Step 1 of Plaid flow — creates a short-lived link token.
    The frontend JavaScript uses this to initialize Plaid Link.

    Returns:
        JSON: { link_token: "..." }
    """
    request = LinkTokenCreateRequest(
        products=[Products("transactions")],
        client_name="Financial AI Assistant",
        country_codes=[CountryCode("US")],
        language="en",
        user=LinkTokenCreateRequestUser(client_user_id="local-user")
    )
    response = client.link_token_create(request)
    return jsonify({"link_token": response.link_token})


@app.route("/exchange_token", methods=["POST"])
def exchange_token():
    """
    Step 3 of Plaid flow — exchanges the temporary public_token
    for a permanent access_token and saves it to disk.

    The public_token is single-use and expires quickly.
    The access_token is permanent and used for all future data pulls.

    Returns:
        JSON: { status: "ok" }
    """
    public_token = request.json["public_token"]

    exchange_request = ItemPublicTokenExchangeRequest(public_token=public_token)
    response = client.item_public_token_exchange(exchange_request)

    # Save access token to file so Streamlit can read it
    with open(TOKEN_PATH, "w") as f:
        f.write(response.access_token)

    return jsonify({"status": "ok"})


if __name__ == "__main__":
    # Runs on port 5000 alongside Streamlit (port 8501)
    app.run(port=5000, debug=True)