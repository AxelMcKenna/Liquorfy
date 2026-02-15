import Foundation

@Observable
final class ProductDetailViewModel {
    var product: Product?
    var isLoading = false
    var error: String?

    private let api = APIClient.shared

    @MainActor
    func loadProduct(id: UUID) async {
        isLoading = true
        error = nil

        do {
            product = try await api.fetchProduct(id: id)
        } catch {
            self.error = error.localizedDescription
        }

        isLoading = false
    }
}
