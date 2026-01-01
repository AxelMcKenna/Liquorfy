export interface Store {
  id: string;
  name: string;
  chain: string;
  lat: number;
  lon: number;
  address?: string | null;
  region?: string | null;
  distance_km?: number | null;
}

export interface StoreListResponse {
  items: Store[];
}

export interface Location {
  lat: number;
  lon: number;
}

export interface Price {
  store_id: string;
  store_name: string;
  chain: string;
  price_nzd: number;
  promo_price_nzd?: number | null;
  promo_text?: string | null;
  promo_ends_at?: string | null;
  is_member_only?: boolean;
  price_per_100ml?: number | null;
  price_per_standard_drink?: number | null;
  standard_drinks?: number | null;
  distance_km?: number | null;
}

export interface Product {
  id: string;
  name: string;
  brand?: string | null;
  category?: string | null;
  chain: string;
  abv_percent?: number | null;
  total_volume_ml?: number | null;
  pack_count?: number | null;
  unit_volume_ml?: number | null;
  image_url?: string | null;
  product_url?: string | null;
  price: Price;
  last_updated: string;
}

export interface ProductListResponse {
  items: Product[];
  total: number;
}

export type Category =
  | "beer"
  | "wine"
  | "spirits"
  | "rtd"
  | "cider"
  | "vodka"
  | "gin"
  | "rum"
  | "whisky"
  | "bourbon"
  | "scotch"
  | "tequila"
  | "brandy"
  | "liqueur"
  | "champagne"
  | "sparkling"
  | "red_wine"
  | "white_wine"
  | "rose"
  | "craft_beer"
  | "lager"
  | "ale"
  | "ipa"
  | "stout"
  | "mixer"
  | "non_alcoholic";

export enum SortOption {
  BEST_VALUE = "price_per_100ml",
  CHEAPEST = "total_price",
  BEST_PER_DRINK = "price_per_standard_drink",
  DISTANCE = "distance",
  NEWEST = "newest"
}

export type ChainType = "super_liquor" | "liquorland" | "bottle_o" | "countdown" | "new_world" | "paknsave" | "liquor_centre" | "glengarry" | "thirsty_liquor" | "black_bull";

export interface ProductFilters {
  query?: string;
  category?: string;
  chains?: ChainType[];
  promo_only?: boolean;
  price_min?: number;
  price_max?: number;
  sort?: SortOption;
  store_ids?: string[];
  lat?: number;
  lon?: number;
  radius_km?: number;
  limit?: number;
  offset?: number;
}
