export type VerticalTheme = "liquor" | "tech" | "home" | "pharma" | "beauty" | "pet";

type ThemePalette = {
  label: string;
  primary: string;
  accent: string;
  ring: string;
  bodyFont: string;
  headingFont: string;
  rootFontSize: string;
  background: string;
  backgroundSecondary: string;
  backgroundTertiary: string;
  card: string;
  popover: string;
};

const DEFAULT_THEME: VerticalTheme = "liquor";
const STORAGE_KEY = "liquorfy.verticalTheme";
const QUERY_PARAM_KEY = "vertical";

const THEME_ALIASES: Record<string, VerticalTheme> = {
  liquor: "liquor",
  liquorfy: "liquor",
  tech: "tech",
  home: "home",
  appliances: "home",
  "home-appliances": "home",
  pharma: "pharma",
  pharmacy: "pharma",
  medical: "pharma",
  beauty: "beauty",
  pet: "pet",
  pets: "pet",
  "pet-goods": "pet",
};

export const VERTICAL_THEME_PALETTES: Record<VerticalTheme, ThemePalette> = {
  liquor: {
    label: "Liquor",
    primary: "158 55% 23%",
    accent: "158 55% 23%",
    ring: "158 55% 23%",
    bodyFont: "\"DM Sans\", -apple-system, BlinkMacSystemFont, \"Segoe UI\", sans-serif",
    headingFont: "\"Lora\", Georgia, serif",
    rootFontSize: "100%",
    background: "42 18% 97%",
    backgroundSecondary: "40 14% 94%",
    backgroundTertiary: "38 10% 91%",
    card: "42 18% 97%",
    popover: "42 18% 97%",
  },
  tech: {
    label: "Tech",
    primary: "224 64% 33%",
    accent: "200 98% 39%",
    ring: "224 64% 33%",
    bodyFont: "\"Space Grotesk\", \"DM Sans\", -apple-system, BlinkMacSystemFont, \"Segoe UI\", sans-serif",
    headingFont: "\"Space Grotesk\", \"DM Sans\", -apple-system, BlinkMacSystemFont, \"Segoe UI\", sans-serif",
    rootFontSize: "100%",
    background: "42 18% 97%",
    backgroundSecondary: "40 14% 94%",
    backgroundTertiary: "38 10% 91%",
    card: "42 18% 97%",
    popover: "42 18% 97%",
  },
  home: {
    label: "Home & Appliances",
    primary: "35 32% 47%",
    accent: "35 37% 58%",
    ring: "35 32% 47%",
    bodyFont: "\"Source Serif 4\", \"Lora\", Georgia, serif",
    headingFont: "\"Cormorant Garamond\", \"Lora\", Georgia, serif",
    rootFontSize: "106.25%",
    background: "40 32% 93%",
    backgroundSecondary: "39 32% 88%",
    backgroundTertiary: "37 33% 81%",
    card: "40 32% 93%",
    popover: "40 32% 93%",
  },
  pharma: {
    label: "Pharma",
    primary: "175 77% 26%",
    accent: "175 84% 32%",
    ring: "175 77% 26%",
    bodyFont: "\"Public Sans\", \"DM Sans\", -apple-system, BlinkMacSystemFont, \"Segoe UI\", sans-serif",
    headingFont: "\"Source Serif 4\", \"Lora\", Georgia, serif",
    rootFontSize: "100%",
    background: "42 18% 97%",
    backgroundSecondary: "40 14% 94%",
    backgroundTertiary: "38 10% 91%",
    card: "42 18% 97%",
    popover: "42 18% 97%",
  },
  beauty: {
    label: "Beauty",
    primary: "333 71% 51%",
    accent: "329 86% 70%",
    ring: "333 71% 51%",
    bodyFont: "\"Plus Jakarta Sans\", \"DM Sans\", -apple-system, BlinkMacSystemFont, \"Segoe UI\", sans-serif",
    headingFont: "\"Cormorant Garamond\", \"Lora\", Georgia, serif",
    rootFontSize: "100%",
    background: "42 18% 97%",
    backgroundSecondary: "40 14% 94%",
    backgroundTertiary: "38 10% 91%",
    card: "42 18% 97%",
    popover: "42 18% 97%",
  },
  pet: {
    label: "Pet Goods",
    primary: "35 38% 39%",
    accent: "35 38% 39%",
    ring: "35 38% 39%",
    bodyFont: "\"Nunito Sans\", \"DM Sans\", -apple-system, BlinkMacSystemFont, \"Segoe UI\", sans-serif",
    headingFont: "\"Merriweather\", \"Lora\", Georgia, serif",
    rootFontSize: "100%",
    background: "42 18% 97%",
    backgroundSecondary: "40 14% 94%",
    backgroundTertiary: "38 10% 91%",
    card: "42 18% 97%",
    popover: "42 18% 97%",
  },
};

const hasOwn = (obj: object, key: string): boolean =>
  Object.prototype.hasOwnProperty.call(obj, key);

const isVerticalTheme = (value: string): value is VerticalTheme =>
  hasOwn(VERTICAL_THEME_PALETTES, value);

const resolveTheme = (rawTheme: string | null | undefined): VerticalTheme | null => {
  if (!rawTheme) return null;

  const normalized = rawTheme.trim().toLowerCase().replace(/_/g, "-").replace(/\s+/g, "-");
  if (isVerticalTheme(normalized)) return normalized;

  return THEME_ALIASES[normalized] ?? null;
};

const getStoredTheme = (): VerticalTheme | null => {
  try {
    return resolveTheme(window.localStorage.getItem(STORAGE_KEY));
  } catch {
    return null;
  }
};

const setStoredTheme = (theme: VerticalTheme): void => {
  try {
    window.localStorage.setItem(STORAGE_KEY, theme);
  } catch {
    // Ignore storage failures (private mode / disabled storage)
  }
};

const getQueryTheme = (): VerticalTheme | null => {
  const queryTheme = new URLSearchParams(window.location.search).get(QUERY_PARAM_KEY);
  return resolveTheme(queryTheme);
};

const getEnvTheme = (): VerticalTheme | null =>
  resolveTheme(import.meta.env.VITE_VERTICAL_THEME as string | undefined);

const getInitialVerticalTheme = (): VerticalTheme => {
  if (typeof window === "undefined") {
    return getEnvTheme() ?? DEFAULT_THEME;
  }

  const queryTheme = getQueryTheme();
  if (queryTheme) {
    setStoredTheme(queryTheme);
    return queryTheme;
  }

  return getStoredTheme() ?? getEnvTheme() ?? DEFAULT_THEME;
};

export const applyVerticalTheme = (theme: VerticalTheme): void => {
  const palette = VERTICAL_THEME_PALETTES[theme];
  const root = document.documentElement;

  root.dataset.verticalTheme = theme;
  root.style.setProperty("--primary", palette.primary);
  root.style.setProperty("--accent", palette.accent);
  root.style.setProperty("--ring", palette.ring);
  root.style.setProperty("--font-body", palette.bodyFont);
  root.style.setProperty("--font-heading", palette.headingFont);
  root.style.setProperty("--root-font-size", palette.rootFontSize);
  root.style.setProperty("--background", palette.background);
  root.style.setProperty("--background-secondary", palette.backgroundSecondary);
  root.style.setProperty("--background-tertiary", palette.backgroundTertiary);
  root.style.setProperty("--card", palette.card);
  root.style.setProperty("--popover", palette.popover);
};

export const initializeVerticalTheme = (): VerticalTheme => {
  const theme = getInitialVerticalTheme();
  applyVerticalTheme(theme);
  return theme;
};
