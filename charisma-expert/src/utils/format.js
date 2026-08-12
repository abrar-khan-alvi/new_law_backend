// Plan quota fields (document_limit, warrant_document_limit) are nullable
// integers on the backend where null means "unlimited" — never -1 or a
// large sentinel number.
export const formatLimit = (value) => (value == null ? 'Unlimited' : value);
