import Foundation

/// Drives the search dropdown, mirroring the web SearchAutocomplete:
/// popular products (shown before typing), and debounced autocomplete suggestions
/// (min 2 chars, 300ms) once the user types.
@MainActor
@Observable
final class AutocompleteViewModel {
    var suggestions: [Suggestion] = []
    var popular: [PopularProduct] = []
    var isLoading = false

    private let api = APIClient.shared
    private var searchTask: Task<Void, Never>?

    private static let minQueryLength = 2
    private static let debounceNanos: UInt64 = 300_000_000

    func loadPopular() async {
        guard popular.isEmpty else { return }
        popular = (try? await api.fetchPopularProducts(limit: 5)) ?? []
    }

    /// Debounced query update. Clears suggestions for short queries.
    func updateQuery(_ query: String) {
        searchTask?.cancel()
        let trimmed = query.trimmingCharacters(in: .whitespacesAndNewlines)
        guard trimmed.count >= Self.minQueryLength else {
            suggestions = []
            isLoading = false
            return
        }

        isLoading = true
        searchTask = Task { [api] in
            try? await Task.sleep(nanoseconds: Self.debounceNanos)
            if Task.isCancelled { return }
            let result = (try? await api.fetchAutocomplete(query: trimmed, limit: 8)) ?? []
            if Task.isCancelled { return }
            self.suggestions = result
            self.isLoading = false
        }
    }

    func clear() {
        searchTask?.cancel()
        suggestions = []
        isLoading = false
    }
}
