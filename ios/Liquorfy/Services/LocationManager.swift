import CoreLocation
import SwiftUI

@Observable
final class LocationManager: NSObject, CLLocationManagerDelegate {
    var location: CLLocationCoordinate2D?
    var locationSource: LocationSource?
    var radiusKm: Double = Constants.Radius.default {
        didSet { cacheLocation() }
    }
    var isLoading = false
    var error: String?
    var authorizationStatus: CLAuthorizationStatus = .notDetermined

    var isLocationSet: Bool { location != nil }

    enum LocationSource: String, Codable {
        case auto, manual
    }

    private let manager = CLLocationManager()
    private let cacheKey = "cachedLocation"

    override init() {
        super.init()
        manager.delegate = self
        manager.desiredAccuracy = kCLLocationAccuracyBest
        authorizationStatus = manager.authorizationStatus
        restoreFromCache()
    }

    // MARK: - Public

    func requestLocation() {
        isLoading = true
        error = nil

        switch manager.authorizationStatus {
        case .notDetermined:
            manager.requestWhenInUseAuthorization()
        case .authorizedWhenInUse, .authorizedAlways:
            manager.requestLocation()
        case .denied, .restricted:
            isLoading = false
            error = "Location permission denied. Please enable in Settings."
        @unknown default:
            isLoading = false
            error = "Unknown location authorization status."
        }
    }

    func setManualLocation(lat: Double, lon: Double) {
        guard NZBoundsValidator.isInNZ(lat: lat, lon: lon) else {
            error = "Please select a location within New Zealand."
            return
        }
        error = nil
        location = CLLocationCoordinate2D(latitude: lat, longitude: lon)
        locationSource = .manual
        cacheLocation()
    }

    func setRadius(_ km: Double) {
        radiusKm = min(Constants.Radius.max, max(Constants.Radius.min, km))
    }

    func clearLocation() {
        location = nil
        locationSource = nil
        error = nil
        UserDefaults.standard.removeObject(forKey: cacheKey)
    }

    // MARK: - CLLocationManagerDelegate

    func locationManager(_ manager: CLLocationManager, didUpdateLocations locations: [CLLocation]) {
        isLoading = false
        guard let loc = locations.last else { return }

        guard NZBoundsValidator.isInNZ(loc) else {
            error = "Liquorfy is currently only available in New Zealand."
            return
        }

        location = loc.coordinate
        locationSource = .auto
        error = nil
        cacheLocation()
    }

    func locationManager(_ manager: CLLocationManager, didFailWithError error: Error) {
        isLoading = false
        if let clError = error as? CLError {
            switch clError.code {
            case .denied:
                self.error = "Location permission denied."
            case .locationUnknown:
                self.error = "Location unavailable. Please try again."
            default:
                self.error = "Failed to get location."
            }
        } else {
            self.error = "Failed to get location."
        }
    }

    func locationManagerDidChangeAuthorization(_ manager: CLLocationManager) {
        authorizationStatus = manager.authorizationStatus

        switch manager.authorizationStatus {
        case .authorizedWhenInUse, .authorizedAlways:
            if isLoading {
                manager.requestLocation()
            }
        case .denied, .restricted:
            isLoading = false
            error = "Location permission denied. Please enable in Settings."
        default:
            break
        }
    }

    // MARK: - Cache

    private struct CachedLocation: Codable {
        let lat: Double
        let lon: Double
        let source: LocationSource
        let radiusKm: Double
        let timestamp: Date
    }

    private func cacheLocation() {
        guard let location else { return }
        let cached = CachedLocation(
            lat: location.latitude,
            lon: location.longitude,
            source: locationSource ?? .auto,
            radiusKm: radiusKm,
            timestamp: Date()
        )
        if let data = try? JSONEncoder().encode(cached) {
            UserDefaults.standard.set(data, forKey: cacheKey)
        }
    }

    private func restoreFromCache() {
        guard let data = UserDefaults.standard.data(forKey: cacheKey),
              let cached = try? JSONDecoder().decode(CachedLocation.self, from: data) else {
            return
        }

        // Only restore if within TTL
        guard Date().timeIntervalSince(cached.timestamp) < Constants.Cache.locationTTL else {
            UserDefaults.standard.removeObject(forKey: cacheKey)
            return
        }

        location = CLLocationCoordinate2D(latitude: cached.lat, longitude: cached.lon)
        locationSource = cached.source
        radiusKm = cached.radiusKm
    }
}
