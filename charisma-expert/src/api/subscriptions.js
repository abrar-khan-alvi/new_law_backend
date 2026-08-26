import axiosInstance from './axiosInstance';

/** GET /api/subscriptions/plans/ — public */
export const listPlans = () =>
  axiosInstance.get('/api/subscriptions/plans/');

/** GET /api/subscriptions/status/ — auth */
export const getSubscriptionStatus = () =>
  axiosInstance.get('/api/subscriptions/status/');

/**
 * POST /api/subscriptions/cancel/ — auth. Cancels at the end of the current
 * billing period (dormant with a clean 503 until Stripe is configured).
 */
export const cancelSubscription = () =>
  axiosInstance.post('/api/subscriptions/cancel/');

/**
 * POST /api/subscriptions/start-trial/ — auth. Legacy endpoint; new accounts
 * automatically receive a 14-day Free Evaluation.
 * @param {string} plan - 'standard' | 'pro'
 */
export const startTrial = (plan) =>
  axiosInstance.post('/api/subscriptions/start-trial/', { plan });

// NOTE: there is no "subscribe" endpoint — going from Free to a paid plan (or
// changing between paid plans) goes through Stripe Checkout / an in-place
// plan change. See src/api/payments.js#createCheckout.
