import Foundation

enum APIEndpoint {
    case products
    case product(UUID)
    case stores

    var path: String {
        switch self {
        case .products: "/products"
        case .product(let id): "/products/\(id)"
        case .stores: "/stores"
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
