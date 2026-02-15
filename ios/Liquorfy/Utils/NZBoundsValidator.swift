import CoreLocation

enum NZBoundsValidator {
    static let latMin: Double = -47
    static let latMax: Double = -34
    static let lonMin: Double = 165
    static let lonMax: Double = 179

    static func isInNZ(lat: Double, lon: Double) -> Bool {
        lat >= latMin && lat <= latMax && lon >= lonMin && lon <= lonMax
    }

    static func isInNZ(_ coordinate: CLLocationCoordinate2D) -> Bool {
        isInNZ(lat: coordinate.latitude, lon: coordinate.longitude)
    }

    static func isInNZ(_ location: CLLocation) -> Bool {
        isInNZ(location.coordinate)
    }

    /// Default center of NZ (roughly Wellington)
    static let nzCenter = CLLocationCoordinate2D(latitude: -41.2865, longitude: 174.7762)
}
