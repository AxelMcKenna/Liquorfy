import Foundation

/// User's saved default filters, mirroring the web `useSavedFilters` hook
/// (localStorage key `liquorfy_saved_filters`). Loaded on Explore when no
/// explicit filters are supplied.
struct SavedFilters: Codable, Equatable {
    var chains: [String]?
    var category: String?
    var promoOnly: Bool?

    enum CodingKeys: String, CodingKey {
        case chains, category
        case promoOnly = "promo_only"
    }
}

@MainActor
final class SavedFiltersManager {
    static let shared = SavedFiltersManager()

    private let key = "liquorfy_saved_filters"

    func get() -> SavedFilters? {
        guard let data = UserDefaults.standard.data(forKey: key) else { return nil }
        return try? JSONDecoder().decode(SavedFilters.self, from: data)
    }

    func save(_ filters: SavedFilters) {
        if let data = try? JSONEncoder().encode(filters) {
            UserDefaults.standard.set(data, forKey: key)
        }
    }

    func clear() {
        UserDefaults.standard.removeObject(forKey: key)
    }
}
