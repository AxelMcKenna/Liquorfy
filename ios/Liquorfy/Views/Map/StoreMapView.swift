import MapKit
import SwiftUI

struct StoreMapView: View {
    let stores: [Store]
    let userLocation: CLLocationCoordinate2D?
    let radiusKm: Double

    @State private var selectedStore: Store?
    @State private var cameraPosition: MapCameraPosition = .automatic

    var body: some View {
        Map(position: $cameraPosition, selection: $selectedStore) {
            // User location
            UserAnnotation()

            // Radius circle
            if let userLocation {
                MapCircle(
                    center: userLocation,
                    radius: radiusKm * 1000
                )
                .foregroundStyle(.tint.opacity(0.08))
                .stroke(.tint.opacity(0.3), lineWidth: 1)
            }

            // Store markers
            ForEach(stores) { store in
                if let coordinate = store.coordinate {
                    Annotation(store.name, coordinate: coordinate, anchor: .bottom) {
                        StoreAnnotationView(chain: store.chain)
                    }
                    .tag(store)
                }
            }
        }
        .mapStyle(.standard(pointsOfInterest: .excludingAll))
        .mapControls {
            MapUserLocationButton()
            MapCompass()
            MapScaleView()
        }
        .onChange(of: userLocation?.latitude) {
            updateCamera()
        }
        .onChange(of: radiusKm) {
            updateCamera()
        }
        .sheet(item: $selectedStore) { store in
            StoreCalloutView(store: store)
                .presentationDetents([.height(180)])
                .presentationDragIndicator(.visible)
        }
        .onAppear {
            updateCamera()
        }
    }

    private func updateCamera() {
        guard let userLocation else { return }
        let region = MKCoordinateRegion(
            center: userLocation,
            latitudinalMeters: radiusKm * 1000 * 2.2,
            longitudinalMeters: radiusKm * 1000 * 2.2
        )
        withAnimation(.easeInOut(duration: 0.5)) {
            cameraPosition = .region(region)
        }
    }
}

#if DEBUG
#Preview {
    StoreMapView(
        stores: PreviewData.stores,
        userLocation: CLLocationCoordinate2D(latitude: -41.2865, longitude: 174.7762),
        radiusKm: 20
    )
    .frame(height: 400)
}
#endif
