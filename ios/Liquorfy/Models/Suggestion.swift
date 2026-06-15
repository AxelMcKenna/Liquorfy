import Foundation

/// Autocomplete suggestion from `GET /products/autocomplete`. Mirrors the web
/// `Suggestion` type.
struct Suggestion: Codable, Identifiable, Hashable, Sendable {
    let id: UUID
    let name: String
    let brand: String?
    let category: String?
    let imageUrl: String?
    let chain: String
    let score: Double

    enum CodingKeys: String, CodingKey {
        case id, name, brand, category, chain, score
        case imageUrl = "image_url"
    }
}
