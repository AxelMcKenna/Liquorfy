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

    private let api = APIClient.shared

    @MainActor
    func fetchAlerts() async {
        isLoading = true
        error = nil
        defer { isLoading = false }

        do {
            alerts = try await api.fetchAlerts().items
        } catch {
            self.error = error.localizedDescription
        }
    }

    @MainActor
    func createAlert(productId: UUID, thresholdPrice: Double?, alertOnPromo: Bool) async throws {
        _ = try await api.createAlert(
            productId: productId,
            thresholdPrice: thresholdPrice,
            alertOnPromo: alertOnPromo
        )
        await fetchAlerts()
    }

    /// PATCH /alerts/{id} — update threshold, promo flag, or active state (matches web).
    @MainActor
    func updateAlert(
        id: UUID,
        thresholdPrice: Double? = nil,
        alertOnPromo: Bool? = nil,
        active: Bool? = nil
    ) async throws {
        _ = try await api.updateAlert(
            id: id,
            thresholdPrice: thresholdPrice,
            alertOnPromo: alertOnPromo,
            active: active
        )
        await fetchAlerts()
    }

    @MainActor
    func deleteAlert(id: UUID) async throws {
        try await api.deleteAlert(id: id)
        alerts.removeAll { $0.id == id }
    }
}
