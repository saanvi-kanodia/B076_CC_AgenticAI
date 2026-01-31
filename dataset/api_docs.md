# NexusCommerce Headless API - V2 Documentation

**Version:** 2.4.0 | **Last Updated:** Oct 15, 2023

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
2. Navigate to **Settings > Developers > Tokens**.
   - *(Note: Legacy documentation previously referenced `Settings > General > API Keys`. This path was deprecated in UI update v2.1 but may still appear in older PDF guides. The correct path is now under the "Developers" tab.)*
3. Click "Create New Token".

### Headers

Include the following headers in all requests:

```http
Authorization: Bearer <YOUR_API_TOKEN>
Content-Type: application/json
Accept: application/json
```

### CORS (Cross-Origin Resource Sharing)

If you are calling the API directly from a browser (e.g., a React storefront), you must whitelist your domain.

1. Go to **Settings > Security > Allowed Origins**.
2. Add your full domain (e.g., `https://www.mystore.com` and `https://staging.mystore.com`).
3. **Localhost:** For local development, you must explicitly add `http://localhost:3000`.

**Common Error:** If you receive a 403 Forbidden on an OPTIONS preflight request, it means the Origin header sent by the browser does not match any entry in your Allowed Origins whitelist.

---

## 3. Rate Limiting

To ensure platform stability, we enforce rate limits based on your plan tier.

| Plan | Limit (Requests/sec) | Burst |
|------|----------------------|-------|
| Starter | 5 | 10 |
| Pro | 20 | 50 |
| Enterprise | 50 | 100 |

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

| Code | Meaning | Typical Cause |
|------|---------|---------------|
| 400 | Bad Request | JSON syntax error or Schema Validation failed (e.g., sending V1 fields to V2). |
| 401 | Unauthorized | Missing or invalid Bearer Token. |
| 403 | Forbidden | CORS error (domain not whitelisted) or insufficient scope. |
| 404 | Not Found | Resource doesn't exist or is archived (>18 months old). |
| 429 | Too Many Requests | You exceeded your plan's rate limit. Check headers. |
| 500 | Internal Error | Platform bug or outage. Contact Support. |
| 502 | Bad Gateway | Webhook delivery failed (your server refused connection). |

---

**NexusCommerce Developer Support** - copyright 2023
