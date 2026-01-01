import { Location } from "@/types";

interface ReverseGeocodeResult {
  address: string;
  suburb?: string;
  city?: string;
  region?: string;
}

/**
 * Reverse geocode a location to get a human-readable address
 * Uses Nominatim (OpenStreetMap) API
 */
export async function reverseGeocode(
  location: Location
): Promise<ReverseGeocodeResult | null> {
  try {
    const response = await fetch(
      `https://nominatim.openstreetmap.org/reverse?` +
        `format=json&lat=${location.lat}&lon=${location.lon}&zoom=14&addressdetails=1`,
      {
        headers: {
          "User-Agent": "Liquorfy/1.0",
        },
      }
    );

    if (!response.ok) {
      console.error("Reverse geocoding failed:", response.statusText);
      return null;
    }

    const data = await response.json();

    if (!data || data.error) {
      console.error("Reverse geocoding error:", data?.error);
      return null;
    }

    // Extract relevant address components
    const address = data.address || {};
    const suburb = address.suburb || address.neighbourhood || address.hamlet;
    const city =
      address.city || address.town || address.village || address.municipality;
    const region = address.state || address.region;

    // Build a concise address string
    const parts = [suburb, city, region].filter(Boolean);
    const addressString = parts.length > 0 ? parts.join(", ") : data.display_name;

    return {
      address: addressString,
      suburb,
      city,
      region,
    };
  } catch (error) {
    console.error("Error reverse geocoding:", error);
    return null;
  }
}

/**
 * Format a location as a short human-readable string
 */
export function formatLocationString(
  geocode: ReverseGeocodeResult | null,
  location: Location
): string {
  if (geocode) {
    return geocode.address;
  }
  // Fallback to coordinates
  return `${location.lat.toFixed(4)}, ${location.lon.toFixed(4)}`;
}
