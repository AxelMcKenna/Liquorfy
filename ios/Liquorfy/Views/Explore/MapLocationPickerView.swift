import SwiftUI
import MapKit

/// Drop-a-pin manual location picker, mirroring the web map pin. The map centre is
/// the chosen point; confirming routes through the same `setManualLocation` path the
/// city picker uses (NZ-bounds validated).
struct MapLocationPickerView: View {
    var onConfirmed: () -> Void

    @Environment(LocationManager.self) private var locationManager
    @Environment(\.dismiss) private var dismiss

    // Default to Auckland until we can centre on any existing location.
    private static let defaultCenter = CLLocationCoordinate2D(latitude: -36.8485, longitude: 174.7633)

    @State private var position: MapCameraPosition = .region(
        MKCoordinateRegion(
            center: MapLocationPickerView.defaultCenter,
            span: MKCoordinateSpan(latitudeDelta: 0.15, longitudeDelta: 0.15)
        )
    )
    @State private var center = MapLocationPickerView.defaultCenter

    var body: some View {
        ZStack {
            Map(position: $position)
                .onMapCameraChange { context in
                    center = context.region.center
                }
                .ignoresSafeArea(edges: .bottom)

            // Fixed centre pin
            Image(systemName: "mappin")
                .font(.system(size: 32))
                .foregroundStyle(.red)
                .offset(y: -16)
                .allowsHitTesting(false)

            VStack {
                Spacer()
                VStack(spacing: 8) {
                    if let error = locationManager.error {
                        Text(error)
                            .font(.appCaption)
                            .foregroundStyle(.red)
                            .multilineTextAlignment(.center)
                    }
                    Button {
                        locationManager.setManualLocation(lat: center.latitude, lon: center.longitude)
                        if locationManager.error == nil {
                            dismiss()
                            onConfirmed()
                        }
                    } label: {
                        Text("Use this location")
                            .font(.appSansSemiBold(size: 16, relativeTo: .body))
                            .foregroundStyle(.white)
                            .frame(maxWidth: .infinity)
                            .frame(height: 48)
                            .background(Color.appPrimary)
                            .clipShape(RoundedRectangle(cornerRadius: 8))
                    }
                    .buttonStyle(.plain)
                }
                .padding(16)
                .background(.thinMaterial)
                .clipShape(RoundedRectangle(cornerRadius: 12))
                .padding()
            }
        }
        .navigationTitle("Drop a Pin")
        .navigationBarTitleDisplayMode(.inline)
        .onAppear {
            if let loc = locationManager.location {
                center = loc
                position = .region(
                    MKCoordinateRegion(
                        center: loc,
                        span: MKCoordinateSpan(latitudeDelta: 0.15, longitudeDelta: 0.15)
                    )
                )
            }
        }
    }
}
