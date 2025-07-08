// Simple session storage utility
export const saveToSession = (key, value) => {
  try {
    sessionStorage.setItem(key, JSON.stringify(value));
  } catch (e) {
    // eslint-disable-next-line no-console
    console.error('Session storage error:', e);
  }
};

export const loadFromSession = (key) => {
  try {
    const item = sessionStorage.getItem(key);
    return item ? JSON.parse(item) : null;
  } catch (e) {
    // eslint-disable-next-line no-console
    console.error('Session storage error:', e);
    return null;
  }
};

export const removeFromSession = (key) => {
  try {
    sessionStorage.removeItem(key);
  } catch (e) {
    // eslint-disable-next-line no-console
    console.error('Session storage error:', e);
  }
};
