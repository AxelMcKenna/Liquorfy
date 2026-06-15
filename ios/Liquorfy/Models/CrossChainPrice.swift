import Foundation

/// A cheaper alternative for the same kind of product sold at a different store/chain.
/// Mirrors the web `CrossChainPrice` type returned inside `ProductDetail`.
struct CrossChainPrice: Codable, Hashable, Identifiable, Sendable {
    let productId: UUID
    let productName: String
    let productUrl: String?
    let imageUrl: String?
    let chain: String
    let storeId: UUID
    let storeName: String
    let priceNzd: Double
    let promoPriceNzd: Double?
    let promoText: String?
    let promoEndsAt: Date?
    let pricePer100ml: Double?
    let pricePerStandardDrink: Double?
    let isMemberOnly: Bool?
    let isStale: Bool?
    let distanceKm: Double?

    var id: UUID { productId }

    enum CodingKeys: String, CodingKey {
        case productId = "product_id"
        case productName = "product_name"
        case productUrl = "product_url"
        case imageUrl = "image_url"
        case chain
        case storeId = "store_id"
        case storeName = "store_name"
        case priceNzd = "price_nzd"
        case promoPriceNzd = "promo_price_nzd"
        case promoText = "promo_text"
        case promoEndsAt = "promo_ends_at"
        case pricePer100ml = "price_per_100ml"
        case pricePerStandardDrink = "price_per_standard_drink"
        case isMemberOnly = "is_member_only"
        case isStale = "is_stale"
        case distanceKm = "distance_km"
    }

    var hasPromo: Bool {
        guard let promo = promoPriceNzd else { return false }
        return promo < priceNzd
    }

    /// The price a shopper actually pays — promo when present, otherwise regular.
    var currentPrice: Double { promoPriceNzd ?? priceNzd }

    var savingsPercent: Int {
        guard hasPromo, let promo = promoPriceNzd else { return 0 }
        return Int(((priceNzd - promo) / priceNzd) * 100)
    }

    var savingsAmount: Double {
        guard hasPromo, let promo = promoPriceNzd else { return 0 }
        return priceNzd - promo
    }
}
