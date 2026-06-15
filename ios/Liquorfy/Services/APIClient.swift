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
    private let encoder: JSONEncoder

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
        // Body property names are already snake_case, so default key strategy is correct.
        self.encoder = JSONEncoder()
    }

    // MARK: - Products

    func fetchProducts(filters: ProductFilters) async throws -> ProductListResponse {
        guard let url = APIEndpoint.products.url(queryItems: filters.queryItems) else {
            throw APIError.invalidURL
        }
        return try await get(url)
    }

    /// Full product detail. Sends location params (matching web) so the response
    /// includes distances, cross-chain options, and other-store prices.
    func fetchProductDetail(
        id: UUID,
        lat: Double? = nil,
        lon: Double? = nil,
        radiusKm: Double? = nil
    ) async throws -> ProductDetail {
        var queryItems: [URLQueryItem] = []
        if let lat { queryItems.append(URLQueryItem(name: "lat", value: String(lat))) }
        if let lon { queryItems.append(URLQueryItem(name: "lon", value: String(lon))) }
        if let radiusKm { queryItems.append(URLQueryItem(name: "radius_km", value: String(radiusKm))) }
        guard let url = APIEndpoint.product(id).url(queryItems: queryItems) else {
            throw APIError.invalidURL
        }
        return try await get(url)
    }

    /// Fire-and-forget view tracking (matches web's untracked POST).
    func trackProductView(id: UUID) async {
        guard let url = APIEndpoint.productView(id).url() else { return }
        _ = try? await send(url, method: "POST")
    }

    func fetchAutocomplete(query: String, limit: Int = 8) async throws -> [Suggestion] {
        let queryItems = [
            URLQueryItem(name: "q", value: query),
            URLQueryItem(name: "limit", value: String(limit)),
        ]
        guard let url = APIEndpoint.autocomplete.url(queryItems: queryItems) else {
            throw APIError.invalidURL
        }
        return try await get(url)
    }

    func fetchPopularProducts(limit: Int = 5) async throws -> [PopularProduct] {
        let queryItems = [URLQueryItem(name: "limit", value: String(limit))]
        guard let url = APIEndpoint.popular.url(queryItems: queryItems) else {
            throw APIError.invalidURL
        }
        return try await get(url)
    }

    /// Batch-fetch enriched products for the given IDs (used by Watchlist favourites).
    func fetchBatchProducts(
        ids: [UUID],
        lat: Double? = nil,
        lon: Double? = nil,
        radiusKm: Double? = nil
    ) async throws -> [Product] {
        guard let url = APIEndpoint.batch.url() else { throw APIError.invalidURL }
        let body = BatchRequest(
            ids: ids.map(\.uuidString),
            lat: lat,
            lon: lon,
            radius_km: radiusKm
        )
        return try await post(url, body: body)
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
        return try await get(url)
    }

    // MARK: - Alerts

    func fetchAlerts() async throws -> AlertListResponse {
        guard let url = APIEndpoint.alerts.url() else { throw APIError.invalidURL }
        return try await get(url)
    }

    @discardableResult
    func createAlert(productId: UUID, thresholdPrice: Double?, alertOnPromo: Bool) async throws -> PriceAlert {
        guard let url = APIEndpoint.alerts.url() else { throw APIError.invalidURL }
        let body = CreateAlertRequest(
            product_id: productId.uuidString,
            threshold_price: thresholdPrice,
            alert_on_promo: alertOnPromo
        )
        return try await post(url, body: body)
    }

    @discardableResult
    func updateAlert(
        id: UUID,
        thresholdPrice: Double? = nil,
        alertOnPromo: Bool? = nil,
        active: Bool? = nil
    ) async throws -> PriceAlert {
        guard let url = APIEndpoint.alert(id).url() else { throw APIError.invalidURL }
        let body = UpdateAlertRequest(
            threshold_price: thresholdPrice,
            alert_on_promo: alertOnPromo,
            active: active
        )
        let data = try await send(url, method: "PATCH", body: try encoder.encode(body))
        return try decodeAs(data)
    }

    func deleteAlert(id: UUID) async throws {
        guard let url = APIEndpoint.alert(id).url() else { throw APIError.invalidURL }
        _ = try await send(url, method: "DELETE")
    }

    // MARK: - User

    func deleteAccount() async throws {
        guard let url = APIEndpoint.userAccount.url() else { throw APIError.invalidURL }
        _ = try await send(url, method: "DELETE")
    }

    // MARK: - Request bodies

    private struct BatchRequest: Encodable {
        let ids: [String]
        let lat: Double?
        let lon: Double?
        let radius_km: Double?
    }

    private struct CreateAlertRequest: Encodable {
        let product_id: String
        let threshold_price: Double?
        let alert_on_promo: Bool
    }

    private struct UpdateAlertRequest: Encodable {
        let threshold_price: Double?
        let alert_on_promo: Bool?
        let active: Bool?
    }

    // MARK: - Generic request plumbing

    private func get<T: Decodable>(_ url: URL) async throws -> T {
        let data = try await send(url)
        return try decodeAs(data)
    }

    private func post<Body: Encodable, T: Decodable>(_ url: URL, body: Body) async throws -> T {
        let data = try await send(url, method: "POST", body: try encoder.encode(body))
        return try decodeAs(data)
    }

    private func decodeAs<T: Decodable>(_ data: Data) throws -> T {
        do {
            return try decoder.decode(T.self, from: data)
        } catch {
            throw APIError.decodingError(error)
        }
    }

    private func send(_ url: URL, method: String = "GET", body: Data? = nil) async throws -> Data {
        do {
            var urlRequest = URLRequest(url: url)
            urlRequest.httpMethod = method

            if let body {
                urlRequest.httpBody = body
                urlRequest.setValue("application/json", forHTTPHeaderField: "Content-Type")
            }

            // Attach Supabase auth token if available
            if let authSession = try? await supabase.auth.session {
                urlRequest.setValue(
                    "Bearer \(authSession.accessToken)",
                    forHTTPHeaderField: "Authorization"
                )
            }

            let (data, response) = try await session.data(for: urlRequest)

            if let http = response as? HTTPURLResponse, !(200...299).contains(http.statusCode) {
                throw APIError.httpError(http.statusCode)
            }

            return data
        } catch let error as APIError {
            throw error
        } catch {
            throw APIError.networkError(error)
        }
    }
}
