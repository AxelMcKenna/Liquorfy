import Foundation
import Observation

/// Recently viewed products, mirroring the web `useRecentlyViewed` hook
/// (localStorage key `liquorfy_recently_viewed`, newest first, capped at 10).
@MainActor
@Observable
final class RecentlyViewedManager {
    static let shared = RecentlyViewedManager()

    private let key = "liquorfy_recently_viewed"
    private let maxItems = 10

    private(set) var products: [Product] = []

    private struct StoredProduct: Codable {
        let product: Product
        let viewedAt: Double
    }

    init() {
        if let data = UserDefaults.standard.data(forKey: key),
           let stored = try? JSONDecoder().decode([StoredProduct].self, from: data) {
            products = stored.map(\.product)
        }
    }

    /// Move a product to the front, de-duplicating by id and capping the list.
    func add(_ product: Product) {
        var next = products.filter { $0.id != product.id }
        next.insert(product, at: 0)
        products = Array(next.prefix(maxItems))
        persist()
    }

    private func persist() {
        // viewedAt is a monotonically-decreasing stamp so the order survives a
        // round-trip, matching the web hook's `Date.now() - i` scheme.
        let now = Date().timeIntervalSince1970 * 1000
        let stored = products.enumerated().map { index, product in
            StoredProduct(product: product, viewedAt: now - Double(index))
        }
        if let data = try? JSONEncoder().encode(stored) {
            UserDefaults.standard.set(data, forKey: key)
        }
    }
}
