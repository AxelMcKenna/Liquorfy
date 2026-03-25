import Foundation

struct PriceAlert: Codable, Identifiable {
    let id: UUID
    let productId: UUID
    let productName: String?
    let thresholdPrice: Double?
    let alertOnPromo: Bool
    let lastTriggeredAt: Date?
    let active: Bool
    let createdAt: Date

    enum CodingKeys: String, CodingKey {
        case id
        case productId = "product_id"
        case productName = "product_name"
        case thresholdPrice = "threshold_price"
        case alertOnPromo = "alert_on_promo"
        case lastTriggeredAt = "last_triggered_at"
        case active
        case createdAt = "created_at"
    }
}

struct AlertListResponse: Codable {
    let items: [PriceAlert]
}

@Observable
final class AlertsViewModel {
    var alerts: [PriceAlert] = []
    var isLoading = false
    var error: String?

    func fetchAlerts() async {
        isLoading = true
        error = nil
        defer { isLoading = false }

        do {
            guard let url = URL(string: Constants.apiBaseURL + "/alerts") else { return }
            var request = URLRequest(url: url)

            if let session = try? await supabase.auth.session {
                request.setValue("Bearer \(session.accessToken)", forHTTPHeaderField: "Authorization")
            }

            let (data, response) = try await URLSession.shared.data(for: request)

            if let http = response as? HTTPURLResponse, !(200...299).contains(http.statusCode) {
                error = "Failed to load alerts"
                return
            }

            let decoder = JSONDecoder()
            decoder.dateDecodingStrategy = .iso8601
            let result = try decoder.decode(AlertListResponse.self, from: data)
            alerts = result.items
        } catch {
            self.error = error.localizedDescription
        }
    }

    func createAlert(productId: UUID, thresholdPrice: Double?, alertOnPromo: Bool) async throws {
        guard let url = URL(string: Constants.apiBaseURL + "/alerts") else { return }
        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")

        if let session = try? await supabase.auth.session {
            request.setValue("Bearer \(session.accessToken)", forHTTPHeaderField: "Authorization")
        }

        var body: [String: Any] = ["product_id": productId.uuidString]
        if let threshold = thresholdPrice {
            body["threshold_price"] = threshold
        }
        body["alert_on_promo"] = alertOnPromo
        request.httpBody = try JSONSerialization.data(withJSONObject: body)

        let (_, response) = try await URLSession.shared.data(for: request)
        if let http = response as? HTTPURLResponse, !(200...299).contains(http.statusCode) {
            throw APIError.httpError(http.statusCode)
        }

        await fetchAlerts()
    }

    func deleteAlert(id: UUID) async throws {
        guard let url = URL(string: Constants.apiBaseURL + "/alerts/\(id)") else { return }
        var request = URLRequest(url: url)
        request.httpMethod = "DELETE"

        if let session = try? await supabase.auth.session {
            request.setValue("Bearer \(session.accessToken)", forHTTPHeaderField: "Authorization")
        }

        let (_, response) = try await URLSession.shared.data(for: request)
        if let http = response as? HTTPURLResponse, !(200...299).contains(http.statusCode) {
            throw APIError.httpError(http.statusCode)
        }

        alerts.removeAll { $0.id == id }
    }
}
