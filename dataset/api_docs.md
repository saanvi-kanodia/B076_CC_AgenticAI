# NexusCommerce Headless API - V2 Documentation

**Version:** 2.4.0 | **Last Updated:** Dec 15, 2023

---

## 1. Introduction

Welcome to the NexusCommerce V2 API. This API is designed for headless commerce implementations, allowing you to build custom storefronts using React, Vue, or mobile frameworks.

### Base URL

- **Production:** `https://api.nexuscommerce.com/v2`
- **Staging:** `https://staging-api.nexuscommerce.com/v2`

---

## 2. Authentication & Security

All API requests must be authenticated using a Bearer Token.

### Generating API Keys

To generate a new API Token:

1. Log in to the Merchant Dashboard.
2. Navigate to **Settings > Developers > API Tokens**.
   - _(Note: Legacy documentation previously referenced `Settings > General > API Keys`. This path was deprecated in UI update v2.1 but may still appear in older PDF guides. The correct path is now under the "Developers" tab.)_
3. Click "Create New Token".
4. Copy the token immediately - it will not be shown again for security.

### Headers

Include the following headers in all requests:

```http
Authorization: Bearer <YOUR_API_TOKEN>
Content-Type: application/json
Accept: application/json
Accept-Version: 2.4.0
```

### Common Authentication Errors

**401 Unauthorized:** Token is missing, expired, or invalid

- Solution: Generate a new token from Settings > Developers > API Tokens

**403 Forbidden:** Token is valid but lacks required permissions

- Solution: Check token permissions in dashboard or generate admin token

### CORS (Cross-Origin Resource Sharing)

If you are calling the API directly from a browser (e.g., a React storefront), you must whitelist your domain.

#### How to Configure CORS:

1. Go to **Settings > Security > CORS Origins**.
2. Add your full domain (e.g., `https://www.mystore.com` and `https://staging.mystore.com`).
3. **Localhost:** For local development, you must explicitly add:
   - `http://localhost:3000`
   - `http://localhost:8080`
   - `https://localhost:3000` (if using HTTPS locally)

#### CORS Troubleshooting:

**Error:** `Access-Control-Allow-Origin header is not present`

- **Cause:** Your domain is not in the CORS whitelist
- **Solution:** Add your exact domain to Settings > Security > CORS Origins

**Error:** `CORS policy: Request header field authorization is not allowed`

- **Cause:** Authorization header not permitted for your origin
- **Solution:** Ensure your origin is whitelisted and supports credentials

**Error:** `Preflight request doesn't pass access control check`

- **Cause:** OPTIONS request blocked
- **Solution:** Add your domain to CORS origins and ensure HTTPS if required

---

## 3. Products API

### Create Product

**Endpoint:** `POST /api/v2/products`

**Headers:**

```http
Authorization: Bearer your_token_here
Content-Type: application/json
```

**Request Body:**

```json
{
  "name": "Running Shoes",
  "description": "High-performance running shoes",
  "price": 129.99,
  "currency": "USD",
  "sku": "RUN-001",
  "images": [
    "https://cdn.example.com/shoe1.jpg",
    "https://cdn.example.com/shoe2.jpg"
  ],
  "category_id": "cat_123",
  "inventory": {
    "quantity": 50,
    "track_quantity": true
  },
  "attributes": {
    "color": "Blue",
    "size": "10",
    "material": "Synthetic"
  }
}
```

### Important Schema Changes (v2.4.0)

⚠️ **BREAKING CHANGES:**

- `product_image` field has been **removed** in v2.4.0
- Use `images` array instead (supports multiple images)
- `images` field must be an **array of strings**, not a single string

**Old Format (DEPRECATED):**

```json
{
  "name": "Product",
  "product_image": "https://example.com/image.jpg" // ❌ No longer supported
}
```

**New Format (REQUIRED):**

```json
{
  "name": "Product",
  "images": ["https://example.com/image.jpg"] // ✅ Correct format
}
```

### Common Product API Errors

**400 Bad Request - Schema Validation Failed: Additional properties not allowed: product_image**

- **Cause:** Using deprecated `product_image` field
- **Solution:** Remove `product_image` and use `images` array instead

**400 Bad Request - Expected array for 'images', got string**

- **Cause:** Sending images as string instead of array
- **Solution:** Wrap image URL in array: `"images": ["url"]` not `"images": "url"`

**422 Unprocessable Entity - SKU already exists**

- **Cause:** Duplicate SKU in your catalog
- **Solution:** Use unique SKU or update existing product

### Update Product

**Endpoint:** `PUT /api/v2/products/{product_id}`

**Request Body:** Same as create, but all fields are optional for partial updates.

### Product Images Management

For products with multiple images, you can also use the dedicated images endpoint:

**Upload Image:** `POST /api/v2/products/{id}/images`
**Delete Image:** `DELETE /api/v2/products/{id}/images/{image_id}`

---

## 4. Orders API

### List Orders

**Endpoint:** `GET /api/v2/orders`

**Query Parameters:**

- `limit` (integer): Number of orders to return (default: 50, max: 200)
- `offset` (integer): Number of orders to skip (for pagination)
- `status` (string): Filter by order status (pending, confirmed, shipped, delivered, cancelled)
- `created_after` (ISO date): Orders created after this date
- `created_before` (ISO date): Orders created before this date
- `merchant_id` (string): Filter by specific merchant (admin only)

**Example:**

```http
GET /api/v2/orders?limit=100&status=confirmed&created_after=2023-01-01T00:00:00Z
Authorization: Bearer your_token_here
```

### Historical Orders & Data Migration

**Issue:** "Where are my old orders?" / "Missing historical data"

By default, the orders endpoint returns orders from the **last 12 months** only. For older orders:

#### Accessing Archived Orders:

**Endpoint:** `GET /api/v2/orders/archive`

**Query Parameters:**

- `year` (required): Specific year (e.g., 2021, 2022)
- `month` (optional): Specific month (1-12)

**Examples:**

```http
# Get all orders from 2021
GET /api/v2/orders/archive?year=2021

# Get orders from January 2022
GET /api/v2/orders/archive?year=2022&month=1
```

#### Alternative: Extended Date Range

```http
# Get orders from specific date range (up to 2 years)
GET /api/v2/orders?created_after=2021-01-01T00:00:00Z&created_before=2023-01-01T00:00:00Z
```

### Order Status Webhooks

If orders are not appearing in your system, verify webhook configuration:

**Webhook Events:**

- `order.created`
- `order.confirmed`
- `order.shipped`
- `order.delivered`
- `order.cancelled`

**Configure Webhooks:**

1. Go to **Settings > Developers > Webhooks**
2. Add your endpoint URL (must be HTTPS)
3. Select events to subscribe to
4. Test the webhook using the "Send Test" button

**Common Webhook Issues:**

- **Webhook not firing:** Check endpoint is publicly accessible and returns 200 OK
- **SSL certificate issues:** Ensure your webhook URL has valid HTTPS certificate
- **Timeout:** Webhook endpoint must respond within 30 seconds

---

## 5. Inventory API

### Get Inventory

**Endpoint:** `GET /api/v2/inventory`

**Query Parameters:**

- `sku` (string): Get inventory for specific SKU
- `product_id` (string): Get inventory for specific product
- `location_id` (string): Get inventory for specific warehouse/location

### Update Inventory

**Endpoint:** `PUT /api/v2/inventory/{sku}`

```json
{
  "quantity": 25,
  "reserved": 5,
  "available": 20
}
```

### Common Inventory Errors

**500 Internal Server Error - Database Connection Pool Exhausted**

- **Cause:** High traffic overloading database connections
- **Type:** Platform issue (not user error)
- **Solution:** Implement exponential backoff retry logic
- **Platform Action:** Engineering team scales connection pool

**404 Not Found - SKU not found**

- **Cause:** SKU doesn't exist in inventory system
- **Solution:** Verify SKU spelling or create product first

---

## 6. Rate Limits & Throttling

### Current Limits

| Endpoint    | Limit      | Window          | Notes                                    |
| ----------- | ---------- | --------------- | ---------------------------------------- |
| Products    | 100/minute | Per API key     | Burst: 200/minute for 1st minute         |
| Orders      | 60/minute  | Per API key     |                                          |
| Inventory   | 120/minute | Per API key     | Higher limit for real-time stock updates |
| Bulk Import | 1 job      | Per store       | Only 1 concurrent bulk import allowed    |
| Webhooks    | 50/minute  | Per webhook URL |                                          |

### Rate Limit Headers

Every response includes rate limit headers:

```http
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 47
X-RateLimit-Reset: 1640995200
X-RateLimit-Window: 60
```

### Handling 429 Rate Limit Exceeded

When you receive a `429 Too Many Requests` response:

1. **Check Retry-After header** (in seconds)
2. **Wait the specified time** before retrying
3. **Implement exponential backoff** for resilience

**Example Retry Logic (JavaScript):**

```javascript
async function apiCallWithRetry(url, options, maxRetries = 3) {
  for (let i = 0; i <= maxRetries; i++) {
    try {
      const response = await fetch(url, options);

      if (response.status === 429) {
        const retryAfter =
          response.headers.get("Retry-After") || Math.pow(2, i);
        await new Promise((resolve) => setTimeout(resolve, retryAfter * 1000));
        continue;
      }

      return response;
    } catch (error) {
      if (i === maxRetries) throw error;
    }
  }
}
```

---

## 7. Error Codes & Troubleshooting

### HTTP Status Codes

| Code | Meaning               | Typical Cause                           | Solution                                  |
| ---- | --------------------- | --------------------------------------- | ----------------------------------------- |
| 400  | Bad Request           | Invalid JSON, schema validation failure | Check request format and required fields  |
| 401  | Unauthorized          | Missing/invalid API token               | Generate new token in dashboard           |
| 403  | Forbidden             | CORS issue, insufficient permissions    | Check CORS whitelist, token permissions   |
| 404  | Not Found             | Resource doesn't exist                  | Verify IDs, check if resource was deleted |
| 422  | Unprocessable Entity  | Business logic error (duplicate SKU)    | Check business rules, fix data conflicts  |
| 429  | Too Many Requests     | Rate limit exceeded                     | Implement retry with exponential backoff  |
| 500  | Internal Server Error | Platform issue                          | Report to support, implement retry logic  |

### Platform Outage Indicators

If you see multiple 5xx errors across different endpoints:

1. **Check Status Page:** [status.nexuscommerce.com](https://status.nexuscommerce.com)
2. **Multiple Merchants Affected:** Likely platform issue
3. **Database Connection Errors:** Infrastructure scaling issue

**Common 500 Error Patterns:**

- "Connection pool exhausted" → Database scaling issue
- "Service unavailable" → Load balancer/service restart
- "Gateway timeout" → Upstream service latency

---

## 8. Migration Guide (v2.3 → v2.4)

### Schema Changes

1. **Products API:**
   - ❌ Remove `product_image` field
   - ✅ Use `images` array instead
2. **Orders API:**
   - ⚠️ Default date range reduced to 12 months
   - ✅ Use `/orders/archive` for historical data

3. **Authentication:**
   - ⚠️ API key location moved to Settings > Developers
   - ✅ Old tokens still work, generate new ones from new location

### Migration Checklist

- [ ] Update product creation to use `images` array
- [ ] Remove `product_image` from all product payloads
- [ ] Update CORS whitelist with new domains
- [ ] Test webhook endpoints are publicly accessible
- [ ] Implement retry logic for 429 rate limits
- [ ] Update order fetching for historical data (use archive endpoint)

---

## 9. SDK & Code Examples

### JavaScript/Node.js

```javascript
const NexusCommerce = require("@nexuscommerce/api");

const client = new NexusCommerce({
  apiKey: "your_api_key_here",
  environment: "production", // or 'staging'
});

// Create product
const product = await client.products.create({
  name: "New Product",
  price: 99.99,
  images: ["https://example.com/image.jpg"],
});

// Handle rate limits automatically
client.setRetryConfig({
  maxRetries: 3,
  retryDelay: 1000,
});
```

### Python

```python
import requests
import time

class NexusAPI:
    def __init__(self, api_key, base_url='https://api.nexuscommerce.com/v2'):
        self.api_key = api_key
        self.base_url = base_url

    def _request(self, method, endpoint, data=None):
        headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json'
        }

        response = requests.request(method, f'{self.base_url}{endpoint}',
                                  json=data, headers=headers)

        # Handle rate limiting
        if response.status_code == 429:
            retry_after = int(response.headers.get('Retry-After', 60))
            time.sleep(retry_after)
            return self._request(method, endpoint, data)

        return response.json()
```

---

## 10. Support & Resources

### Getting Help

1. **Documentation Issues:** Report outdated docs to docs@nexuscommerce.com
2. **Platform Outages:** Check [status.nexuscommerce.com](https://status.nexuscommerce.com)
3. **Integration Support:** Create ticket at [support.nexuscommerce.com](https://support.nexuscommerce.com)
4. **Emergency (Critical Issues):** Call +1-800-NEXUS-911

### Useful Resources

- **Postman Collection:** [Download API Collection](https://docs.nexuscommerce.com/postman)
- **OpenAPI Spec:** [Download Swagger JSON](https://api.nexuscommerce.com/v2/openapi.json)
- **Status Page:** [status.nexuscommerce.com](https://status.nexuscommerce.com)
- **Developer Community:** [community.nexuscommerce.com](https://community.nexuscommerce.com)

### Common Integration Patterns

- **React Storefront:** [View Tutorial](https://docs.nexuscommerce.com/tutorials/react)
- **Vue.js Integration:** [View Tutorial](https://docs.nexuscommerce.com/tutorials/vue)
- **Mobile Apps:** [View Tutorial](https://docs.nexuscommerce.com/tutorials/mobile)
- **Webhook Processing:** [View Tutorial](https://docs.nexuscommerce.com/tutorials/webhooks)

---

_Last updated: December 15, 2023 - Version 2.4.0_

---

## 3. Rate Limiting

To ensure platform stability, we enforce rate limits based on your plan tier.

| Plan       | Limit (Requests/sec) | Burst |
| ---------- | -------------------- | ----- |
| Starter    | 5                    | 10    |
| Pro        | 20                   | 50    |
| Enterprise | 50                   | 100   |

### Rate Limit Headers

Every response includes headers to help you manage traffic:

- **X-RateLimit-Limit:** The ceiling for this timeframe.
- **X-RateLimit-Remaining:** The number of requests left in the current window.
- **X-RateLimit-Reset:** The time at which the current rate limit window resets.

### Behavior

If you exceed the limit, the API returns `429 Too Many Requests`. The response body will include a `Retry-After` header indicating how many seconds to wait.

---

## 4. Migration Guide: V1 to V2 (Breaking Changes)

If you are migrating from our hosted V1 platform to V2 Headless, please note the following critical breaking changes.

### A. Product Images Schema

In V1, a product had a single main image field. In V2, we support multiple media types via an array.

**❌ V1 Payload (Deprecated - Will Return 400):**

```json
{
  "title": "Running Shoe",
  "product_image": "https://cdn.nexus.com/shoe.jpg"
}
```

**✅ V2 Payload (Correct):**

```json
{
  "title": "Running Shoe",
  "images": [
    {
      "url": "https://cdn.nexus.com/shoe.jpg",
      "is_primary": true,
      "alt_text": "Side view"
    }
  ]
}
```

Attempting to send `product_image` will result in: `Schema Validation Failed: Additional properties not allowed`.

### B. Historical Data Access

To improve performance, the V2 standard endpoints (`/orders`, `/invoices`) only return data from the last 18 months.

- **Active Data:** `GET /api/v2/orders/{id}` → Returns 200 for recent orders.
- **Archived Data:** `GET /api/v2/orders/{id}` → Returns 404 Not Found for orders older than 18 months.

**How to access Archive:** You must use the Archive API endpoint: `GET /api/v2/archive/orders/{id}`. This is a slower, cold-storage lookup.

---

## 5. Webhooks

Webhooks allow your backend to react to events (e.g., order placement, inventory updates).

### Payload Format

All webhooks are sent as POST requests with a JSON body.

```json
{
  "event_id": "evt_12345",
  "type": "order.created",
  "created_at": "2023-10-27T10:00:00Z",
  "data": { ... }
}
```

### Timeout Policy

**Crucial:** Your server must respond with a 200 OK status code within 3 seconds.

- If your server takes > 3 seconds, we consider the delivery failed (Timeout).
- If you return 4xx or 5xx, we consider it failed.
- We attempt 3 retries with exponential backoff before disabling the webhook.

### Common Issues

- **404 Not Found:** You changed your backend URL but didn't update the Webhook settings in NexusCommerce.
- **504 Gateway Timeout:** Your script is doing too much work (e.g., sending emails) before returning the 200 OK. **Best Practice:** Queue the work and return 200 immediately.

---

## 6. Resources

### Products

#### Create/Update Product

```
POST /api/v2/products
PUT /api/v2/products/{id}
```

**Body Schema:**

```json
{
  "title": "string (required)",
  "sku": "string (required, unique)",
  "price": "integer (cents)",
  "images": "array of objects",
  "status": "enum['active', 'draft']"
}
```

### Inventory

#### Get Inventory Levels

```
GET /api/v2/inventory
```

**Response:**

```json
{
  "data": [
    {
      "sku": "SKU-101",
      "available": 45,
      "reserved": 2
    }
  ]
}
```

### Service Reliability

The Inventory API is a high-availability service. However, during platform-wide maintenance or severe outages, it may return:

- **500 Internal Server Error:** Database connection failure.
- **503 Service Unavailable:** System under load shedding.

If you see sustained 500 errors across multiple requests, check the Status Page.

---

## 7. Troubleshooting Codes

| Code | Meaning           | Typical Cause                                                                  |
| ---- | ----------------- | ------------------------------------------------------------------------------ |
| 400  | Bad Request       | JSON syntax error or Schema Validation failed (e.g., sending V1 fields to V2). |
| 401  | Unauthorized      | Missing or invalid Bearer Token.                                               |
| 403  | Forbidden         | CORS error (domain not whitelisted) or insufficient scope.                     |
| 404  | Not Found         | Resource doesn't exist or is archived (>18 months old).                        |
| 429  | Too Many Requests | You exceeded your plan's rate limit. Check headers.                            |
| 500  | Internal Error    | Platform bug or outage. Contact Support.                                       |
| 502  | Bad Gateway       | Webhook delivery failed (your server refused connection).                      |

---

**NexusCommerce Developer Support** - copyright 2023
