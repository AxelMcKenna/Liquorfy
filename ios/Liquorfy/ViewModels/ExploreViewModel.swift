import CoreLocation
import Foundation

@Observable
final class ExploreViewModel {
    var products: [Product] = []
    var total: Int = 0
    var currentPage: Int = 1
    var isLoading = false
    var error: String?

    var totalPages: Int {
        guard total > 0 else { return 0 }
        return Int(ceil(Double(total) / Double(Constants.Pagination.defaultPageSize)))
    }

    var pageInfo: String {
        guard total > 0 else { return "No products found" }
        let start = (currentPage - 1) * Constants.Pagination.defaultPageSize + 1
        let end = min(currentPage * Constants.Pagination.defaultPageSize, total)
        return "\(start)-\(end) of \(total)"
    }

    private let api = APIClient.shared

    @MainActor
    func fetchProducts(filters: ProductFilters) async {
        isLoading = true
        error = nil

        do {
            let response = try await api.fetchProducts(filters: filters)
            products = response.items
            total = response.total
            currentPage = response.page
        } catch {
            self.error = error.localizedDescription
            products = []
            total = 0
        }

        isLoading = false
    }
}
