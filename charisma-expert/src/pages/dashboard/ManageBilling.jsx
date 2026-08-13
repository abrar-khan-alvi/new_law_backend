import { useState, useEffect } from 'react';
import { Check, X, Loader2, CreditCard, AlertCircle } from 'lucide-react';
import { cancelSubscription, listPlans, getSubscriptionStatus } from '../../api/subscriptions';
import { createCheckout } from '../../api/payments';
import { formatLimit } from '../../utils/format';

export default function ManageBilling() {
  const [plans, setPlans] = useState([]);
  const [loading, setLoading] = useState(true);
  const [subscription, setSubscription] = useState(null);
  const [checkoutLoadingFor, setCheckoutLoadingFor] = useState(null);
  const [message, setMessage] = useState('');
  const [error, setError] = useState('');

  useEffect(() => {
    Promise.all([
      listPlans().catch(() => ({ data: [] })),
      getSubscriptionStatus().catch(() => ({ data: null }))
    ])
      .then(([plansRes, subRes]) => {
        setPlans(plansRes.data);
        setSubscription(subRes.data);
      })
      .finally(() => setLoading(false));
  }, []);

  const handleCheckout = async (plan) => {
    setMessage('');
    setError('');
    setCheckoutLoadingFor(plan.id);
    try {
      if (plan.name === 'free') {
        const { data } = await cancelSubscription();
        setMessage(data.message || 'Your subscription cancellation has been scheduled.');
        const { data: refreshed } = await getSubscriptionStatus();
        setSubscription(refreshed);
        return;
      }
      const { data } = await createCheckout(plan.name, 'monthly');
      if (data.checkout_url) {
        window.location.href = data.checkout_url;
      } else if (data.subscription) {
        // In-place plan change (prorated upgrade/downgrade without new checkout)
        setSubscription(data.subscription);
        setMessage(data.message || `Successfully changed plan to ${plan.display_name}.`);
      }
    } catch (err) {
      setError(err?.response?.data?.error?.detail || 'Unable to update your subscription.');
    } finally {
      setCheckoutLoadingFor(null);
    }
  };

  if (loading) {
    return (
      <div className="flex justify-center py-20">
        <Loader2 className="animate-spin text-blue-600" size={32} />
      </div>
    );
  }

  // Figure out current plan info
  let currentPlan = subscription?.plan;
  if (!currentPlan && plans.length > 0) {
    currentPlan = [...plans].sort((a, b) => parseFloat(a.price_monthly) - parseFloat(b.price_monthly))[0];
  }

  return (
    <div className="p-8 max-w-6xl mx-auto space-y-8">
      <div>
        <h1 className="text-3xl font-bold text-gray-900 font-serif">Manage Billing</h1>
        <p className="text-gray-500 mt-2">View your current usage and manage your subscription plan.</p>
      </div>

      {message && <div className="rounded-lg border border-emerald-200 bg-emerald-50 px-4 py-3 text-sm text-emerald-800">{message}</div>}
      {error && <div className="rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">{error}</div>}

      {/* Current Plan Overview */}
      <div className="bg-white rounded-2xl border border-gray-200 shadow-sm p-6 flex flex-col md:flex-row md:items-center justify-between gap-6">
        <div className="flex items-center gap-4">
          <div className="w-12 h-12 rounded-full bg-blue-50 flex items-center justify-center text-blue-600 shrink-0">
            <CreditCard size={24} />
          </div>
          <div>
            <p className="text-sm font-semibold text-gray-500 uppercase tracking-wider mb-1">Current Plan</p>
            <h2 className="text-2xl font-bold text-gray-900">{currentPlan?.display_name || 'Free Tier'}</h2>
            <p className="text-sm text-gray-600 mt-1">
              {currentPlan?.name === 'free' 
                ? 'Lifetime Quota - No monthly resets'
                : `Billed ${subscription?.billing_period || 'monthly'} — renews automatically`}
            </p>
          </div>
        </div>
        
        {subscription?.cancel_at_period_end && (
          <div className="bg-amber-50 text-amber-800 px-4 py-3 rounded-lg border border-amber-200 flex items-start gap-3 max-w-md">
            <AlertCircle size={20} className="shrink-0 mt-0.5" />
            <div className="text-sm">
              <p className="font-semibold">Subscription Canceling</p>
              <p>Your subscription will not renew and will end on {new Date(subscription.current_period_end).toLocaleDateString()}.</p>
            </div>
          </div>
        )}
      </div>

      <div className="pt-6">
        <h2 className="text-xl font-bold text-gray-900 mb-6 font-serif">Available Plans</h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 items-stretch">
          {plans.map((plan) => {
            const isCurrentPlan = currentPlan?.id === plan.id;
            const isPopular = plan.name === 'standard';
            const isProcessing = checkoutLoadingFor === plan.id;

            return (
              <div
                key={plan.id}
                className={`relative rounded-2xl border-2 p-8 flex flex-col bg-white ${
                  isCurrentPlan
                    ? 'border-blue-600 shadow-md ring-1 ring-blue-600'
                    : isPopular
                    ? 'border-gray-900 shadow-xl z-10'
                    : 'border-gray-200 shadow-sm'
                }`}
              >
                {isPopular && !isCurrentPlan && (
                  <div className="absolute -top-3.5 left-1/2 -translate-x-1/2">
                    <span className="bg-gray-900 text-white text-xs font-semibold px-3 py-1 rounded-full">
                      Most Popular
                    </span>
                  </div>
                )}
                {isCurrentPlan && (
                  <div className="absolute -top-3.5 left-1/2 -translate-x-1/2">
                    <span className="bg-blue-600 text-white text-xs font-semibold px-3 py-1 rounded-full">
                      Current Plan
                    </span>
                  </div>
                )}

                <div className="mb-6">
                  <h3 className="text-xl font-bold text-gray-900 mb-2">{plan.display_name}</h3>
                  <p className="text-sm text-gray-500 min-h-[40px]">
                    {plan.description || 'Access essential law enforcement tools.'}
                  </p>
                </div>

                <div className="mb-8 flex items-baseline">
                  <span className="text-4xl font-extrabold text-gray-900 tracking-tight">
                    ${plan.price_monthly}
                  </span>
                  <span className="text-gray-500 text-sm font-medium ml-1">/mo</span>
                </div>

                <ul className="space-y-3 mb-8 flex-1">
                  <li className="flex items-center gap-3">
                    <Check size={18} className="text-emerald-500 shrink-0" />
                    <span className="text-sm text-gray-700">AI Incident Reports</span>
                  </li>
                  <li className="flex items-center gap-3">
                    <Check size={18} className="text-emerald-500 shrink-0" />
                    <span className="text-sm text-gray-700">
                      {plan.name === 'free' ? '7 Document Generations — Lifetime' : `${formatLimit(plan.document_limit)} Incident Reports / Month`}
                    </span>
                  </li>
                  {(plan.can_search_warrant || plan.can_arrest_warrant) && plan.name !== 'free' && (
                    <li className="flex items-center gap-3">
                      <Check size={18} className="text-emerald-500 shrink-0" />
                      <span className="text-sm text-gray-700">
                        {formatLimit(plan.warrant_document_limit)} Warrants / Month
                      </span>
                    </li>
                  )}
                  <li className="flex items-center gap-3">
                    {plan.can_search_warrant ? (
                      <Check size={18} className="text-emerald-500 shrink-0" />
                    ) : (
                      <X size={18} className="text-gray-300 shrink-0" />
                    )}
                    <span className={`text-sm ${plan.can_search_warrant ? 'text-gray-700' : 'text-gray-400'}`}>
                      AI Search Warrants
                    </span>
                  </li>
                  <li className="flex items-center gap-3">
                    {plan.can_arrest_warrant ? (
                      <Check size={18} className="text-emerald-500 shrink-0" />
                    ) : (
                      <X size={18} className="text-gray-300 shrink-0" />
                    )}
                    <span className={`text-sm ${plan.can_arrest_warrant ? 'text-gray-700' : 'text-gray-400'}`}>
                      AI Arrest Warrants
                    </span>
                  </li>
                </ul>

                <button
                  disabled={isCurrentPlan || isProcessing}
                  onClick={() => handleCheckout(plan)}
                  className={`w-full py-2.5 rounded-lg text-sm font-semibold transition-colors flex items-center justify-center gap-2 ${
                    isCurrentPlan
                      ? 'bg-blue-50 text-blue-700 cursor-default'
                      : isPopular
                      ? 'bg-gray-900 text-white hover:bg-gray-800'
                      : 'bg-white text-gray-900 border border-gray-300 hover:bg-gray-50'
                  }`}
                >
                  {isProcessing && <Loader2 className="w-4 h-4 animate-spin" />}
                  {isCurrentPlan
                    ? 'Current Plan'
                    : isProcessing
                    ? 'Processing...'
                    : plan.name === 'free'
                    ? 'Downgrade to Free'
                    : 'Choose ' + plan.display_name}
                </button>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}
