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
    let isCheapestNearby: Bool
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
        case isCheapestNearby = "is_cheapest_nearby"
        case lastUpdated = "last_updated"
    }

    /// Description field (present in ProductDetailSchema)
    var description: String? { nil }
}

extension Product {
    // Custom decoder lives in an extension so the synthesized memberwise
    // initializer (used by previews/tests) is preserved.
    init(from decoder: Decoder) throws {
        let c = try decoder.container(keyedBy: CodingKeys.self)
        id = try c.decode(UUID.self, forKey: .id)
        name = try c.decode(String.self, forKey: .name)
        brand = try c.decodeIfPresent(String.self, forKey: .brand)
        category = try c.decodeIfPresent(String.self, forKey: .category)
        chain = try c.decode(String.self, forKey: .chain)
        abvPercent = try c.decodeIfPresent(Double.self, forKey: .abvPercent)
        totalVolumeMl = try c.decodeIfPresent(Double.self, forKey: .totalVolumeMl)
        packCount = try c.decodeIfPresent(Int.self, forKey: .packCount)
        unitVolumeMl = try c.decodeIfPresent(Double.self, forKey: .unitVolumeMl)
        imageUrl = try c.decodeIfPresent(String.self, forKey: .imageUrl)
        productUrl = try c.decodeIfPresent(String.self, forKey: .productUrl)
        price = try c.decode(Price.self, forKey: .price)
        // Tolerate absence (older cached payloads / endpoints predating the field).
        isCheapestNearby = try c.decodeIfPresent(Bool.self, forKey: .isCheapestNearby) ?? false
        lastUpdated = try c.decode(Date.self, forKey: .lastUpdated)
    }
}
