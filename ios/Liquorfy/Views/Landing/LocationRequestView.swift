import SwiftUI

struct LocationRequestView: View {
    @Environment(LocationManager.self) private var locationManager


    var body: some View {
        VStack(spacing: 20) {
            // Icon — matches web: bg-secondary rounded-lg with green MapPin
            Image(systemName: "mappin.and.ellipse")
                .font(.system(size: 24))
                .foregroundStyle(Color.appPrimary)
                .frame(width: 48, height: 48)
                .background(Color.appTertiaryBackground)
                .clipShape(RoundedRectangle(cornerRadius: 8))

            // Title + description
            VStack(spacing: 8) {
                Text("Enable Location")
                    .font(.appSansSemiBold(size: 20, relativeTo: .title3))

                Text("See deals from stores in your area")
                    .font(.appCardBody)
                    .foregroundStyle(.secondary)
                    .multilineTextAlignment(.center)
            }

            if let error = locationManager.error {
                HStack(alignment: .top, spacing: 8) {
                    Image(systemName: "exclamationmark.circle.fill")
                        .foregroundStyle(.red)
                    Text(error)
                        .font(.appCaption)
                        .foregroundStyle(.red)
                }
                .padding(12)
                .frame(maxWidth: .infinity, alignment: .leading)
                .background(Color.red.opacity(0.05))
                .overlay(
                    RoundedRectangle(cornerRadius: 8)
                        .stroke(Color.red.opacity(0.2), lineWidth: 1)
                )
                .clipShape(RoundedRectangle(cornerRadius: 8))
            }

            // Single button — Enable Location
            Button {
                locationManager.requestLocation()
            } label: {
                HStack(spacing: 8) {
                    if locationManager.isLoading {
                        ProgressView()
                            .tint(.white)
                    } else {
                        Image(systemName: "location.fill")
                            .font(.system(size: 16))
                    }
                    Text(locationManager.isLoading ? "Getting location..." : "Enable Location")
                        .font(.appSansSemiBold(size: 16, relativeTo: .body))
                }
                .foregroundStyle(.white)
                .frame(maxWidth: .infinity)
                .frame(height: 52)
                .background(Color.appPrimary)
                .clipShape(RoundedRectangle(cornerRadius: 8))
            }
            .buttonStyle(.plain)
            .disabled(locationManager.isLoading)
        }
        .padding(.vertical, 32)
        .padding(.horizontal, 24)
        .frame(maxWidth: .infinity)
    }
}

// MARK: - NZ Cities

enum NZCity: String, CaseIterable, Identifiable {
    case auckland, wellington, christchurch, hamilton, tauranga, dunedin, palmerston, napier, nelson, queenstown

    var id: String { rawValue }

    var name: String {
        switch self {
        case .auckland: "Auckland"
        case .wellington: "Wellington"
        case .christchurch: "Christchurch"
        case .hamilton: "Hamilton"
        case .tauranga: "Tauranga"
        case .dunedin: "Dunedin"
        case .palmerston: "Palmerston North"
        case .napier: "Napier"
        case .nelson: "Nelson"
        case .queenstown: "Queenstown"
        }
    }

    var lat: Double {
        switch self {
        case .auckland: -36.8485
        case .wellington: -41.2924
        case .christchurch: -43.5321
        case .hamilton: -37.7870
        case .tauranga: -37.6878
        case .dunedin: -45.8788
        case .palmerston: -40.3523
        case .napier: -39.4928
        case .nelson: -41.2706
        case .queenstown: -45.0312
        }
    }

    var lon: Double {
        switch self {
        case .auckland: 174.7633
        case .wellington: 174.7787
        case .christchurch: 172.6362
        case .hamilton: 175.2793
        case .tauranga: 176.1651
        case .dunedin: 170.5028
        case .palmerston: 175.6082
        case .napier: 176.9120
        case .nelson: 173.2840
        case .queenstown: 168.6626
        }
    }
}

#Preview {
    LocationRequestView()
        .environment(LocationManager())
}
