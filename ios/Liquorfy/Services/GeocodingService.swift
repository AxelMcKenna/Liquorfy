import CoreLocation

enum GeocodingService {
    private static let geocoder = CLGeocoder()

    static func reverseGeocode(_ coordinate: CLLocationCoordinate2D) async -> String? {
        let location = CLLocation(latitude: coordinate.latitude, longitude: coordinate.longitude)
        do {
            let placemarks = try await geocoder.reverseGeocodeLocation(location)
            guard let placemark = placemarks.first else { return nil }
            return [placemark.locality, placemark.administrativeArea]
                .compactMap { $0 }
                .joined(separator: ", ")
        } catch {
            return nil
        }
    }
}
