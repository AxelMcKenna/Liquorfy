import Foundation

/// A single point on a product's price-history series. Mirrors the web
/// `PriceHistoryPoint` type returned inside `ProductDetail`.
struct PriceHistoryPoint: Codable, Hashable, Identifiable, Sendable {
    /// ISO 8601 date string (kept as-is, matching the web payload).
    let date: String
    let priceNzd: Double
    let promoPriceNzd: Double?

    var id: String { date }

    enum CodingKeys: String, CodingKey {
        case date
        case priceNzd = "price_nzd"
        case promoPriceNzd = "promo_price_nzd"
    }

    /// The effective price plotted on the chart — promo when present.
    var effectivePrice: Double { promoPriceNzd ?? priceNzd }
}
