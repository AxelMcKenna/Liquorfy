import Foundation
import Observation

/// Local-only favourites, mirroring the web `useFavourites` hook
/// (localStorage key `liquorfy_favourites`, a JSON array of product-id strings).
/// Enriched product data is fetched on demand via `/products/batch`.
@MainActor
@Observable
final class FavouritesManager {
    static let shared = FavouritesManager()

    private let key = "liquorfy_favourites"
    private(set) var favouriteIds: Set<String> = []

    var favouriteCount: Int { favouriteIds.count }

    init() {
        if let stored = UserDefaults.standard.data(forKey: key),
           let ids = try? JSONDecoder().decode([String].self, from: stored) {
            favouriteIds = Set(ids)
        }
    }

    func isFavourite(_ productId: UUID) -> Bool {
        favouriteIds.contains(productId.uuidString)
    }

    func toggle(_ productId: UUID) {
        let id = productId.uuidString
        if favouriteIds.contains(id) {
            favouriteIds.remove(id)
        } else {
            favouriteIds.insert(id)
        }
        persist()
    }

    /// Product ids as UUIDs (for the batch-fetch endpoint).
    var favouriteUUIDs: [UUID] {
        favouriteIds.compactMap(UUID.init)
    }

    private func persist() {
        if let data = try? JSONEncoder().encode(Array(favouriteIds)) {
            UserDefaults.standard.set(data, forKey: key)
        }
    }
}
