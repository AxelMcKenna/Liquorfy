import SwiftUI

struct LocationRequestView: View {
    @Environment(LocationManager.self) private var locationManager

    var body: some View {
        VStack(spacing: 16) {
            Image(systemName: "mappin.circle.fill")
                .font(.system(size: 40))
                .foregroundStyle(.tint)

            Text("Enable Location")
                .font(.headline)

            Text("See deals from stores in your area")
                .font(.subheadline)
                .foregroundStyle(.secondary)

            Button {
                locationManager.requestLocation()
            } label: {
                if locationManager.isLoading {
                    ProgressView()
                        .padding(.horizontal)
                } else {
                    Text("Enable Location")
                }
            }
            .buttonStyle(.borderedProminent)
            .disabled(locationManager.isLoading)

            if let error = locationManager.error {
                Text(error)
                    .font(.caption)
                    .foregroundStyle(.red)
                    .multilineTextAlignment(.center)
            }
        }
        .padding(.vertical, 32)
        .frame(maxWidth: .infinity)
    }
}

#Preview {
    LocationRequestView()
        .environment(LocationManager())
}
