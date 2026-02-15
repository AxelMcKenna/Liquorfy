import Foundation

struct ProductFilters: Sendable {
    var query: String?
    var category: Category?
    var chains: Set<ChainType> = []
    var promoOnly: Bool = false
    var uniqueProducts: Bool = false
    var priceMin: Double?
    var priceMax: Double?
    var sort: SortOption?
    var lat: Double?
    var lon: Double?
    var radiusKm: Double?
    var page: Int = 1
    var pageSize: Int = 24

    var queryItems: [URLQueryItem] {
        var items: [URLQueryItem] = []

        if let query, !query.isEmpty {
            items.append(URLQueryItem(name: "q", value: query))
        }
        if let category {
            items.append(URLQueryItem(name: "category", value: category.rawValue))
        }
        for chain in chains.sorted(by: { $0.rawValue < $1.rawValue }) {
            items.append(URLQueryItem(name: "chain", value: chain.rawValue))
        }
        if promoOnly {
            items.append(URLQueryItem(name: "promo_only", value: "true"))
        }
        if uniqueProducts {
            items.append(URLQueryItem(name: "unique_products", value: "true"))
        }
        if let priceMin {
            items.append(URLQueryItem(name: "price_min", value: String(priceMin)))
        }
        if let priceMax {
            items.append(URLQueryItem(name: "price_max", value: String(priceMax)))
        }
        if let sort {
            items.append(URLQueryItem(name: "sort", value: sort.rawValue))
        }
        if let lat {
            items.append(URLQueryItem(name: "lat", value: String(lat)))
        }
        if let lon {
            items.append(URLQueryItem(name: "lon", value: String(lon)))
        }
        if let radiusKm {
            items.append(URLQueryItem(name: "radius_km", value: String(radiusKm)))
        }
        items.append(URLQueryItem(name: "page", value: String(page)))
        items.append(URLQueryItem(name: "page_size", value: String(pageSize)))

        return items
    }
}
