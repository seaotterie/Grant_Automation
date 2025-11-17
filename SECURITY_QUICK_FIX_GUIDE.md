# Catalynx Security - Quick Fix Guide

**URGENT:** Critical security vulnerabilities detected. Follow this guide for immediate remediation.

---

## 🚨 CRITICAL - Fix Immediately (< 24 hours)

### 1. JWT Secret Key (5 minutes)

**File:** `src/auth/jwt_auth.py`

**Current (Line 20):**
```python
JWT_SECRET_KEY = secrets.token_urlsafe(32)  # BAD - regenerates on restart
```

**Fix:**
```python
import os
from dotenv import load_dotenv

load_dotenv()

JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY')
if not JWT_SECRET_KEY:
    raise ValueError("JWT_SECRET_KEY must be set in .env file")
```

**Create .env file:**
```bash
# Generate strong secret
python3 -c "import secrets; print('JWT_SECRET_KEY=' + secrets.token_urlsafe(64))"

# Add to .env (create this file)
JWT_SECRET_KEY=<paste_generated_key_here>
```

**Add to .gitignore:**
```bash
echo ".env" >> .gitignore
```

---

### 2. Remove Hardcoded Credentials (10 minutes)

**File:** `src/auth/jwt_auth.py` (Lines 62-85)

**Replace `_init_default_users` method:**
```python
def _init_default_users(self):
    """Initialize admin user from environment"""
    admin_password = os.getenv('ADMIN_PASSWORD')
    if not admin_password:
        raise ValueError(
            "ADMIN_PASSWORD must be set in .env file.\n"
            "Generate one with: python -c \"import secrets; print(secrets.token_urlsafe(24))\""
        )

    admin_user = User(
        user_id="admin",
        username="admin",
        email=os.getenv('ADMIN_EMAIL', 'admin@catalynx.local'),
        role="admin",
        hashed_password=self.hash_password(admin_password),
        is_active=True
    )

    self.users[admin_user.username] = admin_user
    logger.info("Admin user initialized from environment")
```

**Add to .env:**
```bash
# Generate strong password
python3 -c "import secrets; print('ADMIN_PASSWORD=' + secrets.token_urlsafe(24))"

# Add to .env
ADMIN_PASSWORD=<paste_generated_password_here>
ADMIN_EMAIL=admin@yourorganization.com
```

**IMPORTANT:** Change this password after first login!

---

### 3. Fix SQL Injection (30 minutes)

**File:** `src/database/query_interface.py`

**Add at top of DatabaseQueryInterface class:**
```python
# Whitelist of allowed sort fields
ALLOWED_SORT_FIELDS = {
    'profiles': {
        'id', 'name', 'created_at', 'updated_at', 'organization_type',
        'ein', 'annual_revenue', 'status'
    },
    'opportunities': {
        'id', 'overall_score', 'discovery_date', 'current_stage',
        'organization_name', 'confidence_level', 'updated_at'
    }
}

ALLOWED_SORT_DIRECTIONS = {'ASC', 'DESC'}

def _validate_sort(self, sort: QuerySort, entity_type: str):
    """Validate sort parameters against whitelist"""
    if not sort:
        return

    allowed = self.ALLOWED_SORT_FIELDS.get(entity_type, set())

    # Validate field
    if sort.field not in allowed:
        raise ValueError(f"Invalid sort field: {sort.field}")

    # Validate direction
    if sort.direction.upper() not in self.ALLOWED_SORT_DIRECTIONS:
        raise ValueError(f"Invalid sort direction: {sort.direction}")

    # Validate secondary sort
    if sort.secondary_field:
        if sort.secondary_field not in allowed:
            raise ValueError(f"Invalid secondary sort field: {sort.secondary_field}")
        if sort.secondary_direction.upper() not in self.ALLOWED_SORT_DIRECTIONS:
            raise ValueError(f"Invalid secondary direction: {sort.secondary_direction}")
```

**Update filter_profiles method (around line 131):**
```python
# Add BEFORE the sorting section
if sort:
    self._validate_sort(sort, 'profiles')

# Now safe to use
if sort:
    base_query += f" ORDER BY {sort.field} {sort.direction.upper()}"
    if sort.secondary_field:
        base_query += f", {sort.secondary_field} {sort.secondary_direction.upper()}"
```

**Update filter_opportunities method (around line 304):**
```python
# Add BEFORE the sorting section
if sort:
    self._validate_sort(sort, 'opportunities')

# Now safe to use
if sort:
    base_query += f" ORDER BY o.{sort.field} {sort.direction.upper()}"
    if sort.secondary_field:
        base_query += f", o.{sort.secondary_field} {sort.secondary_direction.upper()}"
```

---

### 4. Create .env File (5 minutes)

**Create file:** `.env` (in project root)

```bash
# SECURITY - NEVER COMMIT THIS FILE TO GIT

# Application
ENVIRONMENT=development
DEBUG=false

# Authentication
JWT_SECRET_KEY=<generate_with_secrets.token_urlsafe(64)>
JWT_EXPIRATION_HOURS=1
ADMIN_PASSWORD=<generate_with_secrets.token_urlsafe(24)>
ADMIN_EMAIL=admin@yourorganization.com

# Database
DATABASE_PATH=data/catalynx.db

# API Keys (if using external services)
OPENAI_API_KEY=your_key_here
PROPUBLICA_API_KEY=your_key_here

# CORS
ALLOWED_ORIGINS=http://localhost:8000,http://127.0.0.1:8000

# Rate Limiting
RATE_LIMIT_PER_MINUTE=100
```

**Update .gitignore:**
```bash
# Add these lines
.env
.env.local
.env.*.local
*.db
*.db-journal
```

---

## ⚠️ HIGH PRIORITY - Fix Within 1 Week

### 5. Fix XSS Vulnerabilities (1 hour)

**Files:** All JavaScript files using `innerHTML`

**Create utility function in `src/web/static/js/utils.js`:**
```javascript
// HTML sanitization utility
const CatalynxSecurity = {
    /**
     * Escape HTML to prevent XSS
     */
    escapeHtml(unsafe) {
        if (unsafe === null || unsafe === undefined) return '';

        return String(unsafe)
            .replace(/&/g, "&amp;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;")
            .replace(/"/g, "&quot;")
            .replace(/'/g, "&#039;");
    },

    /**
     * Create safe notification
     */
    createNotification(title, message, type = 'info') {
        const notification = document.createElement('div');
        notification.className = `notification notification-${type}`;

        const titleEl = document.createElement('h4');
        titleEl.textContent = title;  // Safe - uses textContent

        const messageEl = document.createElement('p');
        messageEl.textContent = message;  // Safe - uses textContent

        notification.appendChild(titleEl);
        notification.appendChild(messageEl);

        return notification;
    }
};
```

**Replace ALL instances of:**
```javascript
// BAD
element.innerHTML = `<h4>${title}</h4><p>${message}</p>`;

// GOOD
element.innerHTML = `<h4>${CatalynxSecurity.escapeHtml(title)}</h4><p>${CatalynxSecurity.escapeHtml(message)}</p>`;

// BETTER
const notification = CatalynxSecurity.createNotification(title, message, 'success');
container.appendChild(notification);
```

**Or use DOMPurify library:**
```html
<!-- Add to index.html -->
<script src="https://cdn.jsdelivr.net/npm/dompurify@3.0.6/dist/purify.min.js"
        integrity="sha384-..."
        crossorigin="anonymous"></script>

<script>
// Use DOMPurify.sanitize() before innerHTML
element.innerHTML = DOMPurify.sanitize(`<h4>${title}</h4>`);
</script>
```

---

### 6. Fix CORS Configuration (5 minutes)

**File:** `src/web/main.py` (around line 393)

**Current:**
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # DANGEROUS!
    allow_credentials=True,
)
```

**Fix:**
```python
import os

# Get from environment
allowed_origins = os.getenv('ALLOWED_ORIGINS', 'http://localhost:8000').split(',')

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,  # Specific origins only
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization"],
    max_age=3600,
)
```

**Also fix in `src/web/main_modular.py` (line 57)**

---

### 7. Strengthen CSP (15 minutes)

**File:** `src/middleware/security.py` (line 30)

**Replace CSP header:**
```python
"Content-Security-Policy": (
    "default-src 'self'; "
    "script-src 'self' https://cdn.tailwindcss.com https://cdn.jsdelivr.net; "  # Removed unsafe-inline, unsafe-eval
    "style-src 'self' https://cdn.tailwindcss.com https://cdn.jsdelivr.net; "  # Removed unsafe-inline
    "img-src 'self' data: https: blob:; "
    "font-src 'self' https://fonts.gstatic.com https://cdn.jsdelivr.net; "
    "connect-src 'self' ws: wss:; "
    "object-src 'none'; "
    "frame-ancestors 'none'; "
    "base-uri 'self'; "
    "form-action 'self'; "
    "upgrade-insecure-requests; "
    "block-all-mixed-content; "
    "report-uri /api/csp-violations"  # Add CSP violation reporting
),
```

**Add CSP violation reporting endpoint:**
```python
@app.post("/api/csp-violations")
async def csp_violation_report(request: Request):
    """Log CSP violations for monitoring"""
    body = await request.json()
    logger.warning(f"CSP Violation: {body}")
    return {"status": "logged"}
```

**Note:** You may need to move inline scripts to external files.

---

### 8. Add Input Validation (2 hours)

**Create:** `src/web/models/profile_models.py`

```python
from pydantic import BaseModel, Field, validator
from typing import Optional, List
import re

class ProfileCreateRequest(BaseModel):
    """Validated profile creation request"""
    name: str = Field(..., min_length=1, max_length=200)
    organization_type: str = Field(..., regex="^(nonprofit|foundation|government)$")
    ein: Optional[str] = Field(None, regex="^[0-9]{9}$|^[0-9]{2}-[0-9]{7}$")
    website_url: Optional[str] = Field(None, max_length=500)
    mission_statement: Optional[str] = Field(None, max_length=2000)
    annual_revenue: Optional[int] = Field(None, ge=0, le=1000000000000)

    @validator('website_url')
    def validate_url(cls, v):
        if v and not v.startswith(('http://', 'https://')):
            raise ValueError('URL must start with http:// or https://')
        return v

    @validator('ein')
    def validate_ein(cls, v):
        if v:
            ein = v.replace('-', '')
            if len(ein) != 9 or not ein.isdigit():
                raise ValueError('EIN must be 9 digits')
        return v

class ProfileUpdateRequest(ProfileCreateRequest):
    """Profile update with optional fields"""
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    organization_type: Optional[str] = Field(None, regex="^(nonprofit|foundation|government)$")
```

**Update routers to use validation:**
```python
from src.web.models.profile_models import ProfileCreateRequest, ProfileUpdateRequest

@router.post("/api/profiles")
async def create_profile(
    profile_data: ProfileCreateRequest  # Pydantic validates automatically!
):
    # All data is validated and safe to use
    pass
```

---

## 🔧 MEDIUM PRIORITY - Fix Within 2 Weeks

### 9. Add Rate Limiting (1 hour)

**Install dependency:**
```bash
pip install slowapi
```

**File:** `src/web/main.py`

```python
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

# Add after app creation
limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Apply to sensitive endpoints
@app.post("/api/auth/login")
@limiter.limit("5/minute")
async def login(request: Request, ...):
    pass

@app.post("/api/profiles")
@limiter.limit("30/hour")
async def create_profile(request: Request, ...):
    pass
```

---

### 10. Update Dependencies (15 minutes)

```bash
# Update critical packages
pip install --upgrade cryptography PyJWT fastapi pydantic

# Check for vulnerabilities
pip install safety pip-audit
safety check
pip-audit

# Update requirements.txt
pip freeze > requirements.txt
```

---

### 11. Implement Password Policy (30 minutes)

**File:** `src/auth/jwt_auth.py`

```python
import re

class PasswordPolicy:
    """Password strength validation"""

    @staticmethod
    def validate(password: str) -> tuple[bool, str]:
        """Returns (is_valid, error_message)"""
        if len(password) < 12:
            return False, "Password must be at least 12 characters"

        if not re.search(r'[A-Z]', password):
            return False, "Password must contain uppercase letter"

        if not re.search(r'[a-z]', password):
            return False, "Password must contain lowercase letter"

        if not re.search(r'\d', password):
            return False, "Password must contain number"

        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            return False, "Password must contain special character"

        return True, ""

def hash_password(self, password: str) -> str:
    """Hash password with validation"""
    is_valid, error = PasswordPolicy.validate(password)
    if not is_valid:
        raise ValueError(error)

    return pwd_context.hash(password)
```

---

## 📋 Testing Your Fixes

### 1. Test JWT Secret Persistence

```bash
# Start server
python src/web/main.py

# Login and get token
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"YOUR_ADMIN_PASSWORD"}'

# Save the token, then RESTART server

# Try using same token - should still work!
curl http://localhost:8000/api/profiles \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### 2. Test SQL Injection is Fixed

```bash
# This should now return an error instead of executing
curl "http://localhost:8000/api/profiles?sort_by=name;DROP%20TABLE%20profiles--"

# Should see: {"detail": "Invalid sort field: name;DROP TABLE profiles--"}
```

### 3. Test XSS is Fixed

```javascript
// In browser console, try to inject script
fetch('/api/profiles', {method: 'POST', body: JSON.stringify({
    name: '<script>alert("XSS")</script>'
})})

// Script tags should be escaped, not executed
```

---

## 🔒 Security Checklist

After applying fixes:

- [ ] `.env` file created with strong secrets
- [ ] `.env` added to `.gitignore`
- [ ] JWT secret persisted in environment
- [ ] Default credentials removed
- [ ] SQL injection fixed with whitelisting
- [ ] XSS vulnerabilities patched
- [ ] CORS restricted to specific origins
- [ ] CSP strengthened (no unsafe-inline/unsafe-eval)
- [ ] Input validation added with Pydantic
- [ ] Rate limiting implemented
- [ ] Dependencies updated
- [ ] Password policy enforced
- [ ] All fixes tested
- [ ] Security audit report reviewed

---

## 🚀 Deployment Security

Before deploying to production:

1. **Change all default passwords**
2. **Enable HTTPS** (use Let's Encrypt)
3. **Set `DEBUG=false`**
4. **Set `ENVIRONMENT=production`**
5. **Review all CORS origins**
6. **Enable strict CSP**
7. **Set up monitoring and logging**
8. **Create backup procedures**
9. **Document incident response plan**
10. **Run security scan** (`bandit -r src/`)

---

## 📞 Need Help?

If you encounter issues:

1. Review the full **SECURITY_AUDIT_REPORT.md**
2. Check logs for specific error messages
3. Test each fix individually
4. Consult Python/FastAPI security documentation

---

**Last Updated:** November 17, 2025
**Next Security Review:** December 17, 2025
