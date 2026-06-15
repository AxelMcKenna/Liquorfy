import Foundation
import Observation

/// Recent search terms, mirroring the web SearchAutocomplete helpers
/// (localStorage key `liquorfy_recent_searches`, newest first, capped at 5).
@MainActor
@Observable
final class RecentSearchesManager {
    static let shared = RecentSearchesManager()

    private let key = "liquorfy_recent_searches"
    private let maxItems = 5

    private(set) var searches: [String] = []

    init() {
        if let data = UserDefaults.standard.data(forKey: key),
           let stored = try? JSONDecoder().decode([String].self, from: data) {
            searches = stored
        }
    }

    func add(_ query: String) {
        let trimmed = query.trimmingCharacters(in: .whitespacesAndNewlines)
        guard !trimmed.isEmpty else { return }
        var next = searches.filter { $0 != trimmed }
        next.insert(trimmed, at: 0)
        searches = Array(next.prefix(maxItems))
        persist()
    }

    func remove(_ query: String) {
        searches.removeAll { $0 == query }
        persist()
    }

    func clearAll() {
        searches = []
        UserDefaults.standard.removeObject(forKey: key)
    }

    private func persist() {
        if let data = try? JSONEncoder().encode(searches) {
            UserDefaults.standard.set(data, forKey: key)
        }
    }
}
