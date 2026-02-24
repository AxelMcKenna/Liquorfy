import Foundation

struct Price: Codable, Hashable, Sendable {
    let storeId: UUID
    let storeName: String
    let chain: String
    let priceNzd: Double
    let promoPriceNzd: Double?
    let promoText: String?
    let promoEndsAt: Date?
    let pricePer100ml: Double?
    let standardDrinks: Double?
    let pricePerStandardDrink: Double?
    let isMemberOnly: Bool
    let isStale: Bool
    let distanceKm: Double?

    enum CodingKeys: String, CodingKey {
        case storeId = "store_id"
        case storeName = "store_name"
        case chain
        case priceNzd = "price_nzd"
        case promoPriceNzd = "promo_price_nzd"
        case promoText = "promo_text"
        case promoEndsAt = "promo_ends_at"
        case pricePer100ml = "price_per_100ml"
        case standardDrinks = "standard_drinks"
        case pricePerStandardDrink = "price_per_standard_drink"
        case isMemberOnly = "is_member_only"
        case isStale = "is_stale"
        case distanceKm = "distance_km"
    }

    var hasPromo: Bool {
        guard let promo = promoPriceNzd else { return false }
        return promo < priceNzd
    }

    var currentPrice: Double {
        promoPriceNzd ?? priceNzd
    }

    var savingsPercent: Int {
        guard hasPromo, let promo = promoPriceNzd else { return 0 }
        return Int(((priceNzd - promo) / priceNzd) * 100)
    }
}
