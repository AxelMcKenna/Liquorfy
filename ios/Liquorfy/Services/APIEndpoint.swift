import Foundation

enum APIEndpoint {
    case products
    case product(UUID)
    case productView(UUID)
    case autocomplete
    case popular
    case batch
    case stores
    case alerts
    case alert(UUID)
    case userAccount

    var path: String {
        switch self {
        case .products: "/products"
        case .product(let id): "/products/\(id)"
        case .productView(let id): "/products/\(id)/view"
        case .autocomplete: "/products/autocomplete"
        case .popular: "/products/popular"
        case .batch: "/products/batch"
        case .stores: "/stores"
        case .alerts: "/alerts"
        case .alert(let id): "/alerts/\(id)"
        case .userAccount: "/user/account"
        }
    }

    func url(queryItems: [URLQueryItem] = []) -> URL? {
        var components = URLComponents(string: Constants.apiBaseURL + path)
        if !queryItems.isEmpty {
            components?.queryItems = queryItems
        }
        return components?.url
    }
}
