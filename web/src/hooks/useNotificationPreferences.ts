import { useState, useCallback } from 'react';

const STORAGE_KEY = 'liquorfy_notification_prefs';

interface NotificationPreferences {
  weeklyDealsEmail: boolean;
  priceDropAlerts: boolean;
}

const DEFAULTS: NotificationPreferences = {
  weeklyDealsEmail: false,
  priceDropAlerts: true,
};

export const useNotificationPreferences = () => {
  const [prefs, setPrefs] = useState<NotificationPreferences>(() => {
    try {
      const stored = localStorage.getItem(STORAGE_KEY);
      return stored ? { ...DEFAULTS, ...JSON.parse(stored) } : DEFAULTS;
    } catch {
      return DEFAULTS;
    }
  });

  const updatePref = useCallback(<K extends keyof NotificationPreferences>(
    key: K,
    value: NotificationPreferences[K]
  ) => {
    setPrefs((prev) => {
      const next = { ...prev, [key]: value };
      localStorage.setItem(STORAGE_KEY, JSON.stringify(next));
      return next;
    });
  }, []);

  return { prefs, updatePref };
};
