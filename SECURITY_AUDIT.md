# Security Vulnerability Audit Report

**Date:** 2026-02-16
**Repository:** MDE_Endpoint_Pols (Defender XDR Endpoint Policy Manager)

---

## VULN-01: DOM-Based Cross-Site Scripting (XSS) via innerHTML [HIGH]

- **Path:** `static/js/app.js` (lines 20-23, 640-663, 801-817, 827-877, 906-921, 937-988, 1016-1037, 1053-1113, 1141-1148, 1200-1219)
- **Vulnerability:** Data from API responses (policy names, device names, alert titles, query results, error messages, descriptions) is interpolated directly into HTML strings via template literals and assigned to `innerHTML` without any sanitization or escaping. If an attacker can control field values in Azure AD/Intune/Defender (e.g., a malicious policy `displayName` like `<img src=x onerror=alert(1)>`), JavaScript will execute in the browser of any user viewing that data.
- **Affected functions:** `showModal()`, `displayAllPolicies()`, `createPolicyCard()`, `viewPolicyDetails()`, `displayDevices()`, `viewDeviceDetails()`, `displayMachines()`, `viewMachineDetails()`, `displayAlerts()`, `displayQueryResults()`
- **Remediation:** Create a helper function that escapes HTML entities (`<`, `>`, `"`, `'`, `&`) and apply it to every API-sourced value before inserting into HTML. Alternatively, use `textContent` for text-only nodes and `document.createElement()` for DOM construction instead of string-based `innerHTML`.

---

## VULN-02: Open Redirect After Login [MEDIUM]

- **Path:** `app.py:57, 77, 120-121`
- **Vulnerability:** The `login_required` decorator stores `request.url` in the `next` query parameter. The `/login` route stores `request.args.get('next')` into the session. After successful OAuth callback, the app redirects to `session.pop('next')` with no validation. An attacker can craft a URL like `/login?next=https://evil.com` and after the victim authenticates, they are redirected to the attacker's site (potential for credential phishing).
- **Remediation:** Validate that `next_url` is a relative path (starts with `/` and not `//`) before redirecting. Use `urllib.parse.urlparse()` to confirm the host is empty or matches the application's host. Reject any absolute URLs.

---

## VULN-03: Missing Authentication on Cache Clear Endpoint [MEDIUM]

- **Path:** `app.py:309-322`
- **Vulnerability:** The `POST /api/cache/clear` endpoint lacks the `@login_required` decorator. Any unauthenticated user can repeatedly clear the application's in-memory cache, forcing expensive re-fetches from Microsoft Graph and Defender APIs, causing performance degradation or denial of service.
- **Remediation:** Add the `@login_required` decorator to the `clear_cache()` route handler.

---

## VULN-04: OData Filter Injection [MEDIUM]

- **Path:** `modules/defender_client.py:94-96`, `app.py:244`
- **Vulnerability:** The `/api/defender/alerts` endpoint reads `request.args.get('filter')` and passes it directly into the Defender API OData query as `?$filter={filters}` without any validation or sanitization. An attacker could inject arbitrary OData operators to extract data beyond what the UI intends to expose, or cause errors that reveal backend information.
- **Remediation:** Implement an allowlist of permitted OData filter fields and operators. Validate and sanitize the filter string before passing to the API. Alternatively, parse the filter into structured parameters and reconstruct a safe query.

---

## VULN-05: Unrestricted KQL Query Execution [MEDIUM]

- **Path:** `app.py:256-275`, `modules/defender_client.py:103-114`
- **Vulnerability:** The `POST /api/defender/query` endpoint accepts arbitrary KQL (Kusto Query Language) strings from authenticated users and forwards them to the Defender Advanced Hunting API without any validation. While authentication is required, any authenticated user can query any data the application's service principal has access to, potentially accessing data beyond their intended authorization scope.
- **Remediation:** Implement query validation: restrict allowed table names, limit result sizes, add a query timeout, and/or implement a set of pre-defined query templates rather than accepting arbitrary KQL. Log all query executions for audit purposes.

---

## VULN-06: Missing CSRF Protection on POST Endpoints [MEDIUM]

- **Path:** `app.py:256-275` (`POST /api/defender/query`), `app.py:309-322` (`POST /api/cache/clear`)
- **Vulnerability:** The application has no CSRF token mechanism for its API endpoints. Since the app uses session-based authentication with cookies, a malicious website could craft cross-origin POST requests that the browser will send with the user's session cookie, executing KQL queries or clearing cache on behalf of the victim.
- **Remediation:** Implement CSRF tokens using Flask-WTF or a custom CSRF middleware. Alternatively, require a custom header (e.g., `X-Requested-With`) that cross-origin requests cannot set without CORS preflight, and validate it server-side.

---

## VULN-07: Session Cookie Security Misconfiguration [MEDIUM]

- **Path:** `config.py:36-37`, `app.py:17-19`
- **Vulnerability:** Session cookies are not configured with security flags: `SESSION_COOKIE_SECURE` is not set (cookies sent over HTTP), `SESSION_COOKIE_HTTPONLY` is not explicitly enforced, and `SESSION_COOKIE_SAMESITE` is not set. This allows session hijacking via network sniffing on non-HTTPS connections and potential CSRF exploitation.
- **Remediation:** Add the following to the Flask config: `SESSION_COOKIE_SECURE=True` (in production), `SESSION_COOKIE_HTTPONLY=True`, and `SESSION_COOKIE_SAMESITE='Lax'`.

---

## VULN-08: Unstable SECRET_KEY in Multi-Worker Deployments [MEDIUM]

- **Path:** `config.py:31`
- **Vulnerability:** `SECRET_KEY = os.getenv('FLASK_SECRET_KEY', os.urandom(24).hex())`. If `FLASK_SECRET_KEY` is not set, a random key is generated at import time. With gunicorn running 4 workers (Dockerfile:39), each worker process will generate a different secret key, causing sessions to break when requests are handled by different workers. Even in single-worker mode, sessions are invalidated on every restart.
- **Remediation:** Make `FLASK_SECRET_KEY` a required environment variable (add it to `Config.validate()`). Raise an error at startup if it is not set rather than falling back to a random value.

---

## VULN-09: Information Disclosure via Exception Messages [LOW]

- **Path:** `app.py:126, 153, 169, 184, 206, 221, 237, 252, 274, 290, 305, 321`
- **Vulnerability:** Raw `str(e)` exception messages are returned in JSON API responses. These can leak internal paths, stack traces, API error details, Azure AD token errors, and other sensitive implementation details to the client.
- **Remediation:** Return generic error messages to clients (e.g., "An internal error occurred"). Log the full exception server-side for debugging. Only include specific error details in development mode.

---

## VULN-10: Missing Content Security Policy (CSP) Header [LOW]

- **Path:** `wsgi.py:13-19`
- **Vulnerability:** Security headers are set (`X-Frame-Options`, `X-Content-Type-Options`, HSTS) but no `Content-Security-Policy` header is configured. The app loads external scripts from `cdn.jsdelivr.net` and `cdnjs.cloudflare.com` without restriction, and constructs extensive inline HTML via `innerHTML`. A CSP would mitigate the impact of any XSS vulnerabilities.
- **Remediation:** Add a `Content-Security-Policy` header that restricts `script-src` to `'self'` and the specific CDN domains used, and `style-src` similarly. Avoid `'unsafe-inline'` if possible.

---

## VULN-11: CDN Resources Without Subresource Integrity (SRI) [LOW]

- **Path:** `templates/base.html:8-9`
- **Vulnerability:** Font Awesome CSS and Chart.js are loaded from external CDNs without `integrity` attributes. If either CDN is compromised, the attacker could serve malicious code to all application users.
- **Remediation:** Add `integrity="sha384-..."` and `crossorigin="anonymous"` attributes to all `<link>` and `<script>` tags loading external resources.

---

## VULN-12: Security Headers Not Applied in Development Mode [LOW]

- **Path:** `wsgi.py:13-19` vs `app.py:343-353`
- **Vulnerability:** Security headers (`X-Content-Type-Options`, `X-Frame-Options`, HSTS, `X-XSS-Protection`) are only added in `wsgi.py` via an `@app.after_request` handler. When the app is run directly via `python app.py`, these headers are not applied. If developers or ops accidentally run the app directly in production, all security headers are missing.
- **Remediation:** Move the `add_security_headers` after-request handler into `app.py` so it applies regardless of entry point.

---

## VULN-13: Health Endpoint Leaks Configuration Details [LOW]

- **Path:** `app.py:140-154`
- **Vulnerability:** The `/api/health` endpoint is unauthenticated and returns `str(e)` from `Config.validate()` failures, which reveals exactly which environment variables are missing (e.g., `"Missing required environment variables: CLIENT_SECRET"`). This is useful reconnaissance information for an attacker.
- **Remediation:** Return only `{"status": "unhealthy"}` without the specific error details on the unauthenticated health endpoint. Log the details server-side.

---

## VULN-14: Verbose Debug Logging in Production Code [LOW]

- **Path:** `modules/graph_client.py` (lines 239, 249-250, 255-256, 261-263, 267, 271, 278, 283, 287, 290, 294-295, 302-303, 307, 309-311)
- **Vulnerability:** Numerous `print()` statements with `DEBUG:` prefixes expose internal API call details, policy names, counts, data types, and error information to stdout/logs. In production with gunicorn, these appear in access logs and could expose sensitive tenant information.
- **Remediation:** Replace `print()` calls with Python's `logging` module. Set the log level to `WARNING` or `ERROR` in production, and `DEBUG` only in development. Remove or guard all `DEBUG:` print statements.

---

## VULN-15: Logout URL Parameter Not URL-Encoded [LOW]

- **Path:** `modules/user_auth.py:102-105`
- **Vulnerability:** The `post_logout_redirect_uri` is concatenated directly into the logout URL without URL encoding: `f"?post_logout_redirect_uri={post_logout_redirect_uri}"`. If the redirect URI contains special characters (e.g., `&`, `=`), it could break the URL structure or enable parameter injection.
- **Remediation:** Use `urllib.parse.urlencode()` or `urllib.parse.quote()` to properly encode the redirect URI parameter.

---

## Summary

| # | Severity | Vulnerability | Primary File |
|---|----------|--------------|-------------|
| 01 | **HIGH** | DOM-based XSS via innerHTML | `static/js/app.js` |
| 02 | MEDIUM | Open Redirect after login | `app.py` |
| 03 | MEDIUM | Missing auth on cache clear | `app.py` |
| 04 | MEDIUM | OData filter injection | `modules/defender_client.py` |
| 05 | MEDIUM | Unrestricted KQL query execution | `app.py`, `modules/defender_client.py` |
| 06 | MEDIUM | Missing CSRF protection on POST endpoints | `app.py` |
| 07 | MEDIUM | Session cookie security flags not set | `config.py` |
| 08 | MEDIUM | Unstable SECRET_KEY across workers | `config.py` |
| 09 | LOW | Information disclosure via exceptions | `app.py` |
| 10 | LOW | Missing Content Security Policy | `wsgi.py` |
| 11 | LOW | CDN resources without SRI hashes | `templates/base.html` |
| 12 | LOW | Security headers only in wsgi.py | `wsgi.py` |
| 13 | LOW | Health endpoint leaks config details | `app.py` |
| 14 | LOW | Verbose debug logging in production | `modules/graph_client.py` |
| 15 | LOW | Logout URL parameter not encoded | `modules/user_auth.py` |

**Total:** 1 High, 7 Medium, 7 Low
