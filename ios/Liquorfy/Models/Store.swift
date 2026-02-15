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

    enum CodingKeys: String, CodingKey {
        case id, name, chain, lat, lon, address, region
        case distanceKm = "distance_km"
    }

    var coordinate: CLLocationCoordinate2D? {
        guard let lat, let lon else { return nil }
        return CLLocationCoordinate2D(latitude: lat, longitude: lon)
    }
}
