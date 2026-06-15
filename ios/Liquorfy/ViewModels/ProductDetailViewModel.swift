import Foundation

@Observable
final class ProductDetailViewModel {
    var detail: ProductDetail?
    var isLoading = false
    var error: String?

    private let api = APIClient.shared

    /// Convenience accessor for the base product (keeps call sites tidy).
    var product: Product? { detail?.product }

    /// Merged, cheapest-first comparison list across stores and chains.
    var compareEntries: [CompareEntry] {
        guard let detail else { return [] }
        return CompareEntry.merged(from: detail)
    }

    @MainActor
    func load(id: UUID, lat: Double?, lon: Double?, radiusKm: Double?) async {
        isLoading = true
        error = nil

        do {
            let detail = try await api.fetchProductDetail(id: id, lat: lat, lon: lon, radiusKm: radiusKm)
            self.detail = detail
            // Record locally and track the view server-side (fire-and-forget, like web).
            RecentlyViewedManager.shared.add(detail.product)
            Task { await api.trackProductView(id: id) }
        } catch {
            self.error = error.localizedDescription
        }

        isLoading = false
    }
}
