import Foundation
import CoreLocation

struct Store: Codable, Identifiable, Hashable, Sendable {
    let id: UUID
    let name: String
    let chain: String
    let lat: Double?
    let lon: Double?
    let address: String?
    let region: String?
    let distanceKm: Double?
    /// West Auckland Licensing Trust monopoly. When false, the store sits inside the
    /// Portage or Waitakere Trust district and legally cannot sell alcohol.
    let sellsAlcohol: Bool?
    /// "portage" | "waitakere" | nil — matches the web `licensing_trust_area` union.
    let licensingTrustArea: String?

    enum CodingKeys: String, CodingKey {
        case id, name, chain, lat, lon, address, region
        case distanceKm = "distance_km"
        case sellsAlcohol = "sells_alcohol"
        case licensingTrustArea = "licensing_trust_area"
    }

    var coordinate: CLLocationCoordinate2D? {
        guard let lat, let lon else { return nil }
        return CLLocationCoordinate2D(latitude: lat, longitude: lon)
    }
}
