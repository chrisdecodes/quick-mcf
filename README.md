# MCF Backend

A streamlined Amazon Multi-Channel Fulfillment (MCF) backend service built with FastAPI and SQLite. This service handles inventory synchronization, order creation, and status tracking via the Amazon Selling Partner API (SP-API).

## 🚀 Getting Started

1.  **Installation**:
    ```bash
    uv pip install -r pyproject.toml
    ```
2.  **Configuration**:
    Copy `.env.example` to `.env` and fill in your Amazon SP-API credentials.
3.  **Run the App**:
    ```bash
    uv run fastapi dev app/main.py
    ```

---

## 🛠️ Core Features

The backend implements three prioritized features, accessible via standard REST endpoints:

### 1. Fulfillment Order Push
Create a new fulfillment order at Amazon.
*   **Endpoint**: `POST /api/v1/fulfillment/orders`
*   **Action**: Validates the payload and submits the order to Amazon FBA.
*   **Note**: Respects `DRY_RUN=True` in `.env` to avoid real Amazon calls during testing.

### 2. Inventory Sync (Reports API)
Sync your FBA inventory levels to a local database.
*   **Automatic**: Runs every 3 hours (configurable via `INVENTORY_SYNC_INTERVAL_HOURS`).
*   **Manual Trigger**: `POST /api/v1/inventory/sync`
*   **Stored Fields**: Strictly tracks `seller_sku`, `asin`, and `afn_fulfillable_quantity`.

### 3. Order Status Polling
Tracks the lifecycle of your MCF orders.
*   **Automatic**: Runs every 60 minutes (configurable via `ORDER_POLL_INTERVAL_MINUTES`).
*   **Manual Trigger**: `POST /api/v1/orders/sync`
*   **Features**: Specifically captures `fulfillmentShipmentStatus` and maintains a full history of status changes in the local database.

---

## 📦 Project Structure

- `app/services/`: Core business logic for Amazon integrations.
- `app/routers/`: API endpoint definitions (REST architecture).
- `app/models/`: Minimized SQLite database schema.
- `app/jobs.py`: Background synchronization task wrappers.
- `app/amazon_client.py`: Unified SP-API client
