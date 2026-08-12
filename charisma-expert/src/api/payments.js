import axiosInstance from './axiosInstance';

/**
 * POST /api/payments/create-checkout/
 * Body: { plan: string, billing_period: 'monthly'|'yearly' }
 * Returns one of two shapes:
 *  - { checkout_url, session_id } — brand-new Stripe subscription, redirect the browser there.
 *  - { message, subscription } — an existing subscription was changed in place (no redirect needed).
 */
export const createCheckout = (plan, billing_period = 'monthly') =>
  axiosInstance.post('/api/payments/create-checkout/', { plan, billing_period });

/** GET /api/payments/billing-history/ */
export const getBillingHistory = () =>
  axiosInstance.get('/api/payments/billing-history/');
