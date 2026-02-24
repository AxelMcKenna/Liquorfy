import Foundation

enum APIError: LocalizedError {
    case invalidURL
    case httpError(Int)
    case decodingError(Error)
    case networkError(Error)

    var errorDescription: String? {
        switch self {
        case .invalidURL:
            "Invalid URL"
        case .httpError(let code):
            "Server error (\(code))"
        case .decodingError:
            "Failed to parse response"
        case .networkError(let error):
            error.localizedDescription
        }
    }
}

actor APIClient {
    static let shared = APIClient()

    private let session: URLSession
    private let decoder: JSONDecoder

    init(session: URLSession = .shared) {
        self.session = session

        let decoder = JSONDecoder()
        // Handle ISO 8601 dates with fractional seconds
        decoder.dateDecodingStrategy = .custom { decoder in
            let container = try decoder.singleValueContainer()
            let string = try container.decode(String.self)

            let formatter = ISO8601DateFormatter()
            formatter.formatOptions = [.withInternetDateTime, .withFractionalSeconds]
            if let date = formatter.date(from: string) { return date }

            formatter.formatOptions = [.withInternetDateTime]
            if let date = formatter.date(from: string) { return date }

            throw DecodingError.dataCorruptedError(
                in: container,
                debugDescription: "Cannot decode date: \(string)"
            )
        }
        self.decoder = decoder
    }

    // MARK: - Products

    func fetchProducts(filters: ProductFilters) async throws -> ProductListResponse {
        guard let url = APIEndpoint.products.url(queryItems: filters.queryItems) else {
            throw APIError.invalidURL
        }
        return try await request(url)
    }

    func fetchProduct(id: UUID) async throws -> Product {
        guard let url = APIEndpoint.product(id).url() else {
            throw APIError.invalidURL
        }
        return try await request(url)
    }

    // MARK: - Stores

    func fetchNearbyStores(lat: Double, lon: Double, radiusKm: Double? = nil) async throws -> StoreListResponse {
        var queryItems = [
            URLQueryItem(name: "lat", value: String(lat)),
            URLQueryItem(name: "lon", value: String(lon)),
        ]
        if let radiusKm {
            queryItems.append(URLQueryItem(name: "radius_km", value: String(radiusKm)))
        }
        guard let url = APIEndpoint.stores.url(queryItems: queryItems) else {
            throw APIError.invalidURL
        }
        return try await request(url)
    }

    // MARK: - Generic request

    private func request<T: Decodable>(_ url: URL) async throws -> T {
        do {
            let (data, response) = try await session.data(from: url)

            if let http = response as? HTTPURLResponse, !(200...299).contains(http.statusCode) {
                throw APIError.httpError(http.statusCode)
            }

            do {
                return try decoder.decode(T.self, from: data)
            } catch {
                throw APIError.decodingError(error)
            }
        } catch let error as APIError {
            throw error
        } catch {
            throw APIError.networkError(error)
        }
    }
}
