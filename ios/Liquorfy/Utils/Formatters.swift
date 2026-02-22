import SwiftUI

enum Formatters {
    // MARK: - Distance

    enum DistanceThreshold {
        static let close: Double = 2   // km - walking distance
        static let medium: Double = 5  // km - short drive
    }

    static func formatDistance(_ km: Double?) -> String? {
        guard let km else { return nil }
        if km < 1 {
            return "\(Int(km * 1000))m"
        }
        return String(format: "%.1fkm", km)
    }

    static func formatDistanceAway(_ km: Double?) -> String? {
        guard let formatted = formatDistance(km) else { return nil }
        return "\(formatted) away"
    }

    static func distanceColor(_ km: Double?) -> Color {
        guard let km else { return .secondary }
        if km < DistanceThreshold.close { return .distanceClose }
        if km < DistanceThreshold.medium { return .distanceMedium }
        return .secondary
    }

    // MARK: - Price

    static func formatPrice(_ price: Double) -> String {
        String(format: "$%.2f", price)
    }

    static func formatPricePerUnit(_ price: Double, unit: String) -> String {
        "\(formatPrice(price)) per \(unit)"
    }

    // MARK: - Promo

    static func formatPromoEndDate(_ date: Date?) -> String? {
        guard let date else { return nil }

        let now = Date()
        let calendar = Calendar.current
        let days = calendar.dateComponents([.day], from: calendar.startOfDay(for: now), to: calendar.startOfDay(for: date)).day ?? 0

        if days < 0 { return "Expired" }
        if days == 0 { return "Ends today" }
        if days == 1 { return "Ends tomorrow" }
        if days <= 7 { return "\(days)d left" }

        let formatter = DateFormatter()
        formatter.locale = Locale(identifier: "en_NZ")
        formatter.dateFormat = "d MMM"
        return "Ends \(formatter.string(from: date))"
    }

    static func savingsPercent(original: Double, promo: Double?) -> Int {
        guard let promo, promo < original else { return 0 }
        return Int(((original - promo) / original) * 100)
    }

    // MARK: - Category

    static func formatCategory(_ raw: String?) -> String {
        guard let raw else { return "" }
        return raw.replacingOccurrences(of: "_", with: " ").capitalized
    }
}
