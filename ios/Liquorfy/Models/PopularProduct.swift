import Foundation

/// Popular product from `GET /products/popular`. Mirrors the web
/// `PopularProduct` type (shown in the search dropdown before any query).
struct PopularProduct: Codable, Identifiable, Hashable, Sendable {
    let id: UUID
    let name: String
    let brand: String?
    let category: String?
    let imageUrl: String?
    let chain: String
    let viewCount: Int

    enum CodingKeys: String, CodingKey {
        case id, name, brand, category, chain
        case imageUrl = "image_url"
        case viewCount = "view_count"
    }
}
