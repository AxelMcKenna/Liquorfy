import CoreLocation
import Foundation

@Observable
final class LandingViewModel {
    var deals: [Product] = []
    var stores: [Store] = []
    var isLoadingDeals = false
    var isLoadingStores = false
    var error: String?

    private let api = APIClient.shared

    @MainActor
    func loadDeals(location: CLLocationCoordinate2D?, radiusKm: Double) async {
        isLoadingDeals = true
        error = nil

        var filters = ProductFilters(
            promoOnly: true,
            uniqueProducts: true,
            sort: .discount,
            page: 1,
            pageSize: 10
        )

        if let location {
            filters.lat = location.latitude
            filters.lon = location.longitude
            filters.radiusKm = radiusKm
        }

        do {
            let response = try await api.fetchProducts(filters: filters)
            deals = response.items.filter { $0.price.hasPromo }
                .sorted { $0.price.savingsPercent > $1.price.savingsPercent }
        } catch {
            self.error = error.localizedDescription
        }

        isLoadingDeals = false
    }

    @MainActor
    func loadStores(location: CLLocationCoordinate2D, radiusKm: Double) async {
        isLoadingStores = true

        do {
            let response = try await api.fetchNearbyStores(
                lat: location.latitude,
                lon: location.longitude,
                radiusKm: radiusKm
            )
            stores = response.items
        } catch {
            // Stores error is non-critical, don't override deals error
        }

        isLoadingStores = false
    }
}
