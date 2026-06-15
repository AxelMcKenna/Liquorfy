import Foundation

/// Batch-fetches enriched product data for the user's favourite ids, mirroring the
/// web `useFavouriteProducts` hook (`POST /products/batch`).
@MainActor
@Observable
final class FavouritesViewModel {
    var products: [Product] = []
    var isLoading = false
    var error: String?

    private let api = APIClient.shared

    func load(ids: [UUID], lat: Double?, lon: Double?, radiusKm: Double?) async {
        guard !ids.isEmpty else {
            products = []
            return
        }
        isLoading = true
        error = nil
        do {
            products = try await api.fetchBatchProducts(ids: ids, lat: lat, lon: lon, radiusKm: radiusKm)
        } catch {
            self.error = "Failed to load favourites"
            products = []
        }
        isLoading = false
    }
}
