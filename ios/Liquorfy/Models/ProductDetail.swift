import Foundation

/// Full product detail returned by `GET /products/{id}`. Mirrors the web
/// `ProductDetail` type, which extends `Product` with the additional
/// comparison/history fields. The JSON is flat, so the embedded `Product` is
/// decoded from the same payload.
struct ProductDetail: Decodable, Identifiable, Hashable, Sendable {
    let product: Product
    let description: String?
    let otherPrices: [Price]
    let crossChainPrices: [CrossChainPrice]
    let priceHistory: [PriceHistoryPoint]

    var id: UUID { product.id }

    enum CodingKeys: String, CodingKey {
        case description
        case otherPrices = "other_prices"
        case crossChainPrices = "cross_chain_prices"
        case priceHistory = "price_history"
    }

    init(from decoder: Decoder) throws {
        // The base product fields live alongside the detail fields in one flat object.
        product = try Product(from: decoder)

        let c = try decoder.container(keyedBy: CodingKeys.self)
        description = try c.decodeIfPresent(String.self, forKey: .description)
        otherPrices = try c.decodeIfPresent([Price].self, forKey: .otherPrices) ?? []
        crossChainPrices = try c.decodeIfPresent([CrossChainPrice].self, forKey: .crossChainPrices) ?? []
        priceHistory = try c.decodeIfPresent([PriceHistoryPoint].self, forKey: .priceHistory) ?? []
    }

    /// Memberwise initializer for previews/tests (the synthesized one is suppressed
    /// by the custom decoder above).
    init(
        product: Product,
        description: String? = nil,
        otherPrices: [Price] = [],
        crossChainPrices: [CrossChainPrice] = [],
        priceHistory: [PriceHistoryPoint] = []
    ) {
        self.product = product
        self.description = description
        self.otherPrices = otherPrices
        self.crossChainPrices = crossChainPrices
        self.priceHistory = priceHistory
    }
}
