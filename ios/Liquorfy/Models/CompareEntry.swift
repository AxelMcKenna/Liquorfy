import Foundation

/// One unified, store-or-chain agnostic price row so the viewed product, its other
/// stores, and cheaper cross-chain alternatives can be ranked together — cheapest
/// first. Mirrors the web `CompareEntry` in ProductDetail.tsx.
struct CompareEntry: Identifiable, Hashable, Sendable {
    let key: String
    let storeName: String
    let chain: String
    let priceNzd: Double
    let promoPriceNzd: Double?
    let distanceKm: Double?
    /// When set, the row navigates to a different (cheaper) listing.
    let productId: UUID?

    var id: String { key }

    /// Effective price used for ranking — promo when it beats the regular price.
    var effective: Double {
        if let promo = promoPriceNzd, promo < priceNzd { return promo }
        return priceNzd
    }

    var hasPromo: Bool {
        if let promo = promoPriceNzd { return promo < priceNzd }
        return false
    }

    /// Build the merged, cheapest-first comparison list from a product detail,
    /// exactly matching the web ordering (self → other stores → cross-chain, sorted
    /// by effective price ascending).
    static func merged(from detail: ProductDetail) -> [CompareEntry] {
        let price = detail.product.price
        var entries: [CompareEntry] = [
            CompareEntry(
                key: "self-\(price.storeId.uuidString)",
                storeName: price.storeName,
                chain: price.chain,
                priceNzd: price.priceNzd,
                promoPriceNzd: price.promoPriceNzd,
                distanceKm: price.distanceKm,
                productId: nil
            )
        ]

        entries += detail.otherPrices.map { p in
            CompareEntry(
                key: "store-\(p.storeId.uuidString)",
                storeName: p.storeName,
                chain: p.chain,
                priceNzd: p.priceNzd,
                promoPriceNzd: p.promoPriceNzd,
                distanceKm: p.distanceKm,
                productId: nil
            )
        }

        entries += detail.crossChainPrices.map { c in
            CompareEntry(
                key: "chain-\(c.productId.uuidString)-\(c.storeId.uuidString)",
                storeName: c.storeName,
                chain: c.chain,
                priceNzd: c.priceNzd,
                promoPriceNzd: c.promoPriceNzd,
                distanceKm: c.distanceKm,
                productId: c.productId
            )
        }

        return entries.sorted { $0.effective < $1.effective }
    }
}
