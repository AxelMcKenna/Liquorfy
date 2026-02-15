import Foundation

struct Product: Codable, Identifiable, Hashable, Sendable {
    let id: UUID
    let name: String
    let brand: String?
    let category: String?
    let chain: String
    let abvPercent: Double?
    let totalVolumeMl: Double?
    let packCount: Int?
    let unitVolumeMl: Double?
    let imageUrl: String?
    let productUrl: String?
    let price: Price
    let lastUpdated: Date

    enum CodingKeys: String, CodingKey {
        case id, name, brand, category, chain
        case abvPercent = "abv_percent"
        case totalVolumeMl = "total_volume_ml"
        case packCount = "pack_count"
        case unitVolumeMl = "unit_volume_ml"
        case imageUrl = "image_url"
        case productUrl = "product_url"
        case price
        case lastUpdated = "last_updated"
    }

    /// Description field (present in ProductDetailSchema)
    var description: String? { nil }
}
