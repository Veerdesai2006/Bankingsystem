/**
 * SecureBank — Client-Side JavaScript
 *
 * This file handles all JavaScript behaviour:
 * - API calls (fetch to our FastAPI backend)
 * - Form submission with error handling
 * - Logout
 * - UI helpers (show/hide alerts, loading states)
 *
 * ARCHITECTURE NOTE:
 * ───────────────────
 * We use the browser's built-in fetch() API to call our JSON endpoints.
 * The server returns JSON → JavaScript reads the response → updates the page.
 * No page reload needed for auth operations.
 *
 * The JWT cookie is handled AUTOMATICALLY by the browser:
 * - Login  → server sets cookie via Set-Cookie header
 * - Logout → server deletes cookie via Set-Cookie: max-age=0
 * - All requests → browser sends cookie automatically
 *
 * We never touch the JWT in JavaScript (it's HTTP-only).
 */

// ─── Utility Functions ────────────────────────────────────────────────────────

/**
 * Show an alert message in the UI.
 * @param {string} elementId - The ID of the alert div
 * @param {string} message   - The message to display
 * @param {string} type      - 'error' or 'success'
 */
function showAlert(elementId, message, type = 'error') {
  const el = document.getElementById(elementId);
  if (!el) return;
  el.textContent = message;
  el.className = `alert alert-${type} show`;
}

/**
 * Hide an alert element.
 */
function hideAlert(elementId) {
  const el = document.getElementById(elementId);
  if (el) el.classList.remove('show');
}

/**
 * Set a button to its loading state (disabled + spinner).
 * @param {HTMLButtonElement} btn
 * @param {string} loadingText
 */
function setButtonLoading(btn, loadingText = 'Please wait...') {
  btn.disabled = true;
  btn.dataset.originalText = btn.innerHTML;
  btn.innerHTML = `<span class="spinner"></span> ${loadingText}`;
}

/**
 * Restore a button from loading state.
 */
function resetButton(btn) {
  btn.disabled = false;
  btn.innerHTML = btn.dataset.originalText || btn.innerHTML;
}

/**
 * Extract error detail from a FastAPI error response.
 * FastAPI returns: { "detail": "message" } or { "detail": [{...}] }
 */
async function getErrorMessage(response) {
  try {
    const data = await response.json();
    if (typeof data.detail === 'string') return data.detail;
    if (Array.isArray(data.detail)) {
      return data.detail.map(e => e.msg).join(', ');
    }
    return 'An unexpected error occurred.';
  } catch {
    return `Server error (${response.status})`;
  }
}

// ─── Authentication ───────────────────────────────────────────────────────────

/**
 * Register a new account.
 * Called by the register form's onsubmit.
 */
async function handleRegister(event) {
  event.preventDefault();
  const form = event.target;
  const btn  = form.querySelector('button[type="submit"]');

  hideAlert('register-alert');
  setButtonLoading(btn, 'Creating account...');

  const email    = document.getElementById('email').value.trim();
  const password = document.getElementById('password').value;
  const confirm  = document.getElementById('confirm-password').value;

  // Client-side validation
  if (password !== confirm) {
    showAlert('register-alert', 'Passwords do not match.');
    resetButton(btn);
    return;
  }
  if (password.length < 8) {
    showAlert('register-alert', 'Password must be at least 8 characters.');
    resetButton(btn);
    return;
  }

  try {
    const response = await fetch('/api/v1/auth/register', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password }),
    });

    if (response.ok) {
      // Registration successful → redirect to login
      showAlert('register-alert', 'Account created! Redirecting to login...', 'success');
      setTimeout(() => { window.location.href = '/login?registered=1'; }, 1200);
    } else {
      const message = await getErrorMessage(response);
      showAlert('register-alert', message);
      resetButton(btn);
    }
  } catch (error) {
    showAlert('register-alert', 'Network error. Please check your connection.');
    resetButton(btn);
  }
}

/**
 * Log in to an existing account.
 * Called by the login form's onsubmit.
 */
async function handleLogin(event) {
  event.preventDefault();
  const form = event.target;
  const btn  = form.querySelector('button[type="submit"]');

  hideAlert('login-alert');
  setButtonLoading(btn, 'Signing in...');

  const email    = document.getElementById('email').value.trim();
  const password = document.getElementById('password').value;

  try {
    const response = await fetch('/api/v1/auth/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password }),
      credentials: 'include', // Important: include cookies in the request
    });

    if (response.ok) {
      // Server set the HTTP-only cookie automatically.
      // We just need to navigate to the dashboard.
      window.location.href = '/dashboard';
    } else {
      const message = await getErrorMessage(response);
      showAlert('login-alert', message);
      resetButton(btn);
    }
  } catch (error) {
    showAlert('login-alert', 'Network error. Please check your connection.');
    resetButton(btn);
  }
}

/**
 * Log out the current user.
 * Calls the logout endpoint which deletes the cookie, then redirects.
 */
async function logout() {
  try {
    await fetch('/api/v1/auth/logout', {
      method: 'POST',
      credentials: 'include',
    });
  } finally {
    // Always redirect, even if the request fails
    window.location.href = '/';
  }
}

// ─── Banking Operations ───────────────────────────────────────────────────────

/**
 * Submit a deposit.
 */
async function handleDeposit(event) {
  event.preventDefault();
  const form = event.target;
  const btn  = form.querySelector('button[type="submit"]');

  hideAlert('deposit-alert');
  setButtonLoading(btn, 'Processing...');

  const amount      = document.getElementById('amount').value;
  const description = document.getElementById('description')?.value || null;

  try {
    const response = await fetch('/api/v1/banking/deposit', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ amount: parseFloat(amount), description }),
      credentials: 'include',
    });

    if (response.ok) {
      const data = await response.json();
      // Show success result
      document.getElementById('result-card').classList.add('show');
      document.getElementById('result-balance').textContent =
        `₹${parseFloat(data.balance_after).toFixed(2)}`;
      form.reset();
      showAlert('deposit-alert', `✓ Deposit of ₹${parseFloat(data.amount).toFixed(2)} successful!`, 'success');
    } else {
      const message = await getErrorMessage(response);
      if (response.status === 401) {
        window.location.href = '/login';
        return;
      }
      showAlert('deposit-alert', message);
    }
  } catch (error) {
    showAlert('deposit-alert', 'Network error. Please try again.');
  } finally {
    resetButton(btn);
  }
}

/**
 * Submit a withdrawal.
 */
async function handleWithdraw(event) {
  event.preventDefault();
  const form = event.target;
  const btn  = form.querySelector('button[type="submit"]');

  hideAlert('withdraw-alert');
  setButtonLoading(btn, 'Processing...');

  const amount      = document.getElementById('amount').value;
  const description = document.getElementById('description')?.value || null;

  try {
    const response = await fetch('/api/v1/banking/withdraw', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ amount: parseFloat(amount), description }),
      credentials: 'include',
    });

    if (response.ok) {
      const data = await response.json();
      document.getElementById('result-card').classList.add('show');
      document.getElementById('result-balance').textContent =
        `₹${parseFloat(data.balance_after).toFixed(2)}`;
      form.reset();
      showAlert('withdraw-alert', `✓ Withdrawal of ₹${parseFloat(data.amount).toFixed(2)} successful!`, 'success');
    } else {
      const message = await getErrorMessage(response);
      if (response.status === 401) {
        window.location.href = '/login';
        return;
      }
      showAlert('withdraw-alert', message);
    }
  } catch (error) {
    showAlert('withdraw-alert', 'Network error. Please try again.');
  } finally {
    resetButton(btn);
  }
}

// ─── Page Init ────────────────────────────────────────────────────────────────

/**
 * Check URL params on login page (e.g., show success message after registration).
 */
function initLoginPage() {
  const params = new URLSearchParams(window.location.search);
  if (params.get('registered') === '1') {
    showAlert('login-alert', '✓ Account created successfully! Please log in.', 'success');
  }
}

// Run page-specific init on load
document.addEventListener('DOMContentLoaded', () => {
  if (document.getElementById('login-alert')) initLoginPage();
});
