import Foundation

struct ProductListResponse: Codable, Sendable {
    let items: [Product]
    let total: Int
    let page: Int
    let pageSize: Int

    enum CodingKeys: String, CodingKey {
        case items, total, page
        case pageSize = "page_size"
    }
}
