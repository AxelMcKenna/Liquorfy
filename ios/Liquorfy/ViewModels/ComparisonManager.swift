import Foundation

@Observable
final class ComparisonManager {
    private(set) var products: [Product] = []

    var count: Int { products.count }
    var isAtLimit: Bool { products.count >= Constants.Comparison.maxProducts }
    var isEmpty: Bool { products.isEmpty }

    func contains(_ product: Product) -> Bool {
        products.contains(where: { $0.id == product.id })
    }

    func toggle(_ product: Product) {
        if let index = products.firstIndex(where: { $0.id == product.id }) {
            products.remove(at: index)
        } else if !isAtLimit {
            products.append(product)
        }
    }

    func remove(_ product: Product) {
        products.removeAll(where: { $0.id == product.id })
    }

    func clear() {
        products.removeAll()
    }

    func sortedByPrice() -> [Product] {
        products.sorted { $0.price.currentPrice < $1.price.currentPrice }
    }
}
