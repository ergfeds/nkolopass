# MeSomb API — Full Integration Guide & SDK Examples

**Base host (domain):** `https://mesomb.hachther.com/`

**Canonical collect endpoint (full URL):** `POST https://mesomb.hachther.com/api/v1.1/payment/collect/`

> Note: some deployments use `/api/v1.1/...` while others may use `/v1.1/...`. Use the `/api` prefix if your installation exposes it (the examples in this doc use `/api/v1.1`). Keep the trailing slash consistent with the server (this doc uses `.../collect/`).

---

## Contents
1. Overview
2. Authentication (SDKs vs direct HTTP)
3. Collect endpoint — full spec
4. Response shapes (success + errors)
5. Examples: cURL, Python (`pymesomb`), Node.js, PHP
6. Webhooks (asynchronous flows & verification)
7. Best practices — nonce, idempotency, fees, conversion, logging, retries
8. Debugging & common errors
9. Postman import snippet
10. Next steps / exports available

---

## 1) Overview
The MeSomb **Collect** endpoint requests a payment from a customer’s mobile/digital wallet (MTN, ORANGE, AIRTEL). It supports synchronous and asynchronous flows, customer/product/location metadata for analytics, currency conversion, and optional web redirect for web-based checkout flows.

Use the official SDKs when possible (they handle authentication, nonce generation and signature). If you must call the HTTP endpoint directly, implement the required header signing mechanism your MeSomb instance expects.

---

## 2) Authentication

### Using official SDKs (recommended)
SDKs (e.g., `pymesomb` for Python) expect three credentials from your MeSomb dashboard:
- `application_key`
- `access_key`
- `secret_key`

Instantiate the SDK client with those keys and call the `make_collect` method. The SDK handles nonce generation, request signing and headers.

### Direct HTTP (only if SDK unavailable)
If calling the HTTP API directly, follow your platform's authentication/signing scheme. Typical patterns:
- Send a request timestamp + unique `nonce`.
- Sign the request body (or canonical string of method + path + nonce + timestamp) with your `secret_key` using HMAC-SHA256.
- Include identifying keys in headers, e.g.:
  - `X-Application-Key: <application_key>`
  - `X-Access-Key: <access_key>`
  - `X-Nonce: <nonce>`
  - `X-Signature: <hmac-signature>`
  - `Content-Type: application/json`

**Important:** Never send your secret key in the request body. Keep secrets server-side.

---

## 3) Collect endpoint — Full spec

**URL**  
`POST https://mesomb.hachther.com/api/v1.1/payment/collect/`  

**Content-Type:** `application/json`  
**Auth:** SDK-managed or header signing (see Authentication)

### Purpose
Start/trigger a collect transaction against a mobile money account.

### Request body — fields

**Required:**
- `nonce` — **string** — **required**  
  Unique token to prevent replay attacks. Use cryptographically-random values and never reuse.

- `payer` — **string** — **required**  
  Target payer account number in **local format** (example for Cameroon: `670000000`).

- `amount` — **double** — **required**  
  Amount to collect.

- `service` — **enum** — **required**  
  Payment service: `MTN` | `ORANGE` | `AIRTEL`.

**Optional / recommended:**
- `mode` — **enum** — `synchronous` (default) | `asynchronous`  
  For slow provider flows, use `asynchronous` and rely on webhooks for final status.

- `fees` — **boolean** — default `true`  
  If `false`, extra fees will be **added** to the amount the payer pays.

- `currency` — **string** — default `XAF`  
  Currency ISO code (local or foreign).

- `country` — **enum** — default `CM`  
  Example values: `CM`, `NE`.

- `conversion` — **boolean**  
  If `true`, MeSomb will convert the amount if the payer uses a foreign currency.

- `trxID` or `trx_id` — **string**  
  Your local transaction id used for reconciliation / idempotency (recommended).

- `operation` — **enum** — default `PAYMENT`  
  Denotes the logical operation name.

- `message` — **string | null**  
  Optional message to send to the customer (SMS/notification).

- `reference` — **string**  
  Friendly tag/name for the transaction (useful for dashboards).

- `redirect` — **uri | null**  
  Redirect URL for web checkout flows after successful payment.

**Nested objects:**

- `customer` — **object** (all fields optional; included for analytics)
  - `email` — email | nullable
  - `phone` — string | nullable
  - `first_name`, `last_name`, `town`, `region`, `country`, `address1`, `address2`

- `location` — **object**
  - `location.town` — string
  - `location.region` — string | nullable
  - `location.country` — string | nullable
  - `location.ip` — string (optional IP for geolocation)

- `products` — **array of objects** — used for product-level analytics
  - `products[].id` — string
  - `products[].name` — string **(recommended required)**
  - `products[].category` — string
  - `products[].quantity` — integer (default: 1)
  - `products[].amount` — double (subtotal)

### Minimal valid example (JSON)
```json
{
  "nonce": "nonce-12345-abcdef",
  "payer": "670000000",
  "amount": 1000.0,
  "service": "MTN",
  "trxID": "local_txn_0001"
}
```

---

## 4) Response shapes

### Success — HTTP 200 (example)
```json
{
  "message": "…",
  "success": true,
  "redirect": "https://example.com",
  "transaction": {
    "pk": "123e4567-e89b-12d3-a456-426614174000",
    "status": "SUCCESS",
    "type": "COLLECT",
    "amount": 1,
    "fees": 1,
    "b_party": "…",
    "message": "…",
    "service": "MTN",
    "reference": "…",
    "ts": "2025-02-06T18:20:52.148Z",
    "direction": -1,
    "country": "CM",
    "currency": "XAF",
    "customer": { /* ... */ },
    "products": [ /* ... */ ],
    "location": { /* ... */ },
    "trxamount": 1,
    "fin_trx_id": "…",
    "name": "…"
  },
  "status": "SUCCESS"
}
```
Key fields to track:
- `transaction.pk` — internal transaction UUID
- `transaction.status` — `SUCCESS`, `FAILED`, `PENDING`
- `transaction.fin_trx_id` — financial provider's transaction id (if provided)
- `redirect` — optional redirect URL

### Errors — HTTP 4xx / 5xx (example)
```json
{
  "detail": "…",
  "code": "subscriber-internal-error",
  "support": "https://example.com"
}
```
- `detail` — human-readable message
- `code` — machine-friendly error code
- `support` — URL for help or documentation

---

## 5) Examples

### cURL (raw; replace auth headers as required)
```bash
curl -X POST "https://mesomb.hachther.com/api/v1.1/payment/collect/" \
  -H "Content-Type: application/json" \
  -H "X-Application-Key: <application_key>" \
  -H "X-Access-Key: <access_key>" \
  -H "X-Nonce: <nonce>" \
  -H "X-Signature: <computed-hmac-signature>" \
  -d '{
    "nonce":"nonce-123",
    "payer":"670000000",
    "amount":100,
    "service":"MTN",
    "trxID":"local-123"
  }'
```

### Python — using `pymesomb` (recommended)
```python
from pymesomb.operations import PaymentOperation
from pymesomb.utils import RandomGenerator

application_key = '<your application key>'
access_key = '<your access key>'
secret_key = '<your secret key>'

client = PaymentOperation(application_key, access_key, secret_key)

response = client.make_collect(
    amount=100,
    service='MTN',
    payer='670000000',
    trx_id='local_txn_1',
    nonce=RandomGenerator.nonce(),
    customer={
        'phone': '+237677550439',
        'email': 'fisher.bank@gmail.com',
        'first_name': 'Fisher',
        'last_name': 'Bank'
    },
    location={
        'town': 'Douala',
        'region': 'Littoral',
        'country': 'Cameroun'
    },
    products=[{
        'id': 'SKU001',
        'name': 'Sac a Main',
        'category': 'Sac'
    }]
)

print("Operation success:", response.is_operation_success())
print("Transaction success:", response.is_transaction_success())
```

### Node.js (fetch) — server-side example
```js
import fetch from "node-fetch";

const BASE = "https://mesomb.hachther.com";
const ENDPOINT = "/api/v1.1/payment/collect/";
const url = BASE + ENDPOINT;

async function collectPayment(body, headers) {
  const res = await fetch(url, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      ...headers
    },
    body: JSON.stringify(body)
  });
  return res.json();
}

// Usage example omitted; include headers with keys and signature
```

### PHP (cURL) — server-side
```php
<?php
$url = "https://mesomb.hachther.com/api/v1.1/payment/collect/";
$payload = json_encode([
  "nonce" => "nonce-abc123",
  "payer" => "670000000",
  "amount" => 100,
  "service" => "MTN",
  "trxID" => "local-0001"
]);

$ch = curl_init($url);
curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);
curl_setopt($ch, CURLOPT_HTTPHEADER, [
    "Content-Type: application/json",
    "X-Application-Key: <application_key>",
    "X-Access-Key: <access_key>",
    "X-Nonce: nonce-abc123",
    "X-Signature: <hmac-signature>",
]);
curl_setopt($ch, CURLOPT_POST, true);
curl_setopt($ch, CURLOPT_POSTFIELDS, $payload);
$response = curl_exec($ch);
if (curl_errno($ch)) {
    echo "Curl error: " . curl_error($ch);
}
curl_close($ch);
echo $response;
```

---

## 6) Webhooks (asynchronous flows)

When you use `mode=asynchronous` or when provider callbacks are required, implement webhooks to receive transaction updates.

### Recommended webhook contract
- Endpoint example: `POST https://yourapp.com/webhooks/mesomb/`
- Expect JSON body like:
```json
{
  "event": "transaction.updated",
  "transaction": { /* full transaction object */ },
  "meta": {
    "pk": "123e4567-...",
    "status": "SUCCESS",
    "ts": "2025-02-06T18:20:52.148Z"
  }
}
```

### Verify webhooks
- Verify webhook signatures (HMAC-SHA256) using the `secret_key` or a webhook-specific secret.
- Sender should include a header such as `X-Mesomb-Signature: sha256=<signature>` (actual header name may vary).
- Compute HMAC-SHA256 over the raw POST body and compare securely (constant-time compare).

Example pseudocode (Node.js):
```js
import crypto from 'crypto';

function verifySignature(rawBody, signatureHeader, webhookSecret) {
  const expected = 'sha256=' + crypto.createHmac('sha256', webhookSecret).update(rawBody).digest('hex');
  return crypto.timingSafeEqual(Buffer.from(expected), Buffer.from(signatureHeader));
}
```

---

## 7) Best practices

- **Use the SDK** whenever possible — it handles nonce, signatures, retries and parsing.
- **Nonces:** generate cryptographically strong nonces; never reuse.
- **trxID:** always send a `trxID` from your system for idempotency and reconciliation.
- **Logging:** log outgoing requests (full payload, masked secrets), request id, response, status codes, `transaction.pk` and `fin_trx_id`.
- **Retries:** for network errors or 5xx responses, implement exponential backoff. For 4xx errors, do not retry automatically.
- **Fees:** clearly display to users whether fees are included or added to payer. If `fees=false`, fees are added to the payer.
- **Currency:** store the `currency` and any conversion rates returned. If `conversion=true`, record conversion details for accounting.
- **Security:** keep secret keys server-side only. Never embed secrets in client-side code.
- **Validation:** validate phone numbers to the expected local format before calling the API (e.g., Cameroon local format `6XXXXXXXX`).
- **Testing:** run flows with testing credentials if available. Validate webhooks before marking transactions final.

---

## 8) Debugging & common errors

- `subscriber-internal-error` — Often external provider error. Log full `detail`, `code`, `ts`, and your `trxID`; contact MeSomb support with these.
- `invalid-nonce` / `replay-detected` — Nonce reused or invalid; generate new nonce.
- `invalid-phone` — Payer number not in expected local format. Normalize before sending.
- `insufficient-funds` or `provider-declined` — Provider specific; present message to user and log `transaction.pk`.
- `timeout`, `gateway-unavailable` — Retry with backoff and check for async webhook updates.
- `signature-mismatch` (for webhooks) — Wrong webhook secret or altered body; use raw body for verification.

---

## 9) Postman import (quick JSON skeleton)

Paste the JSON below into Postman `Import -> Raw Text` to create a basic collection (replace placeholders):

```json
{
  "info": {
    "name": "MeSomb Collect - Quick",
    "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json"
  },
  "item": [
    {
      "name": "Collect Payment",
      "request": {
        "method": "POST",
        "header": [
          { "key": "Content-Type", "value": "application/json" },
          { "key": "X-Application-Key", "value": "<application_key>" },
          { "key": "X-Access-Key", "value": "<access_key>" }
        ],
        "body": {
          "mode": "raw",
          "raw": "{\n  \"nonce\": \"nonce-123\",\n  \"payer\": \"670000000\",\n  \"amount\": 100,\n  \"service\": \"MTN\",\n  \"trxID\": \"local-123\"\n}"
        },
        "url": {
          "raw": "https://mesomb.hachther.com/api/v1.1/payment/collect/",
          "protocol": "https",
          "host": ["mesomb","hachther","com"],
          "path": ["api","v1.1","payment","collect",""]
        }
      }
    }
  ]
}
```

---

## 10) Next steps & optional extras I can provide
- Export this reference as a **PDF** (one-page quick ref + full doc).
- Create a full **Postman collection** (complete examples for collect + webhook verification + status check if you provide the status endpoint path).
- Generate a **Node.js NPM wrapper** (tiny client) that wraps collect + signature creation.
- Produce a **one-page printable quick reference** for onboarding devs.
- Add sample **webhook verification middleware** for Express (Node) or Flask (Python).

---

> **How to download**: the document is available in the canvas on the right. Click the three-dot menu (or the canvas options) and choose **Export / Download** and select **Markdown (.md)** to download this file. If you want, I can also export a ready-made `.md` file here for direct download.

If you'd like any changes (shorter quick reference, company header, links to your dashboard, or Postman file generation), tell me and I'll update the canvas document.

