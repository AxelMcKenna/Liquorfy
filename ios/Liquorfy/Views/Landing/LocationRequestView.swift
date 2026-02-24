import SwiftUI

struct LocationRequestView: View {
    @Environment(LocationManager.self) private var locationManager

    @State private var showManualPicker = false
    @State private var selectedCity: NZCity?

    var body: some View {
        VStack(spacing: 20) {
            // Icon
            Image(systemName: "mappin.and.ellipse")
                .font(.system(size: 24))
                .foregroundStyle(Color.appPrimary)
                .frame(width: 48, height: 48)
                .background(Color.appTertiaryBackground)
                .clipShape(RoundedRectangle(cornerRadius: 8))

            // Title + description
            VStack(spacing: 8) {
                Text("Enable Location")
                    .font(.appSerif(size: 20, relativeTo: .title3))

                Text("See deals from stores in your area")
                    .font(.appCardBody)
                    .foregroundStyle(.primary.opacity(0.55))
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

            if !showManualPicker {
                // Enable Location button
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

                // Show manual option when permission is denied or location failed
                if locationManager.error != nil {
                    Button {
                        withAnimation { showManualPicker = true }
                    } label: {
                        HStack(spacing: 8) {
                            Image(systemName: "map")
                                .font(.system(size: 16))
                            Text("Set Location Manually")
                                .font(.appSansSemiBold(size: 16, relativeTo: .body))
                        }
                        .foregroundStyle(Color.appPrimary)
                        .frame(maxWidth: .infinity)
                        .frame(height: 52)
                        .background(.white)
                        .clipShape(RoundedRectangle(cornerRadius: 8))
                        .overlay(
                            RoundedRectangle(cornerRadius: 8)
                                .stroke(Color.appPrimary.opacity(0.3), lineWidth: 1)
                        )
                    }
                    .buttonStyle(.plain)
                }
            } else {
                // Manual city picker
                VStack(alignment: .leading, spacing: 12) {
                    Text("Select your city")
                        .font(.appSansSemiBold(size: 14, relativeTo: .subheadline))
                        .foregroundStyle(.secondary)

                    LazyVGrid(columns: [
                        GridItem(.flexible()),
                        GridItem(.flexible()),
                    ], spacing: 8) {
                        ForEach(NZCity.allCases) { city in
                            Button {
                                selectedCity = city
                            } label: {
                                Text(city.name)
                                    .font(.appSansMedium(size: 14, relativeTo: .subheadline))
                                    .foregroundStyle(selectedCity == city ? .white : .primary)
                                    .frame(maxWidth: .infinity)
                                    .frame(height: 40)
                                    .background(selectedCity == city ? Color.appPrimary : .white)
                                    .clipShape(RoundedRectangle(cornerRadius: 8))
                                    .overlay(
                                        RoundedRectangle(cornerRadius: 8)
                                            .stroke(selectedCity == city ? Color.clear : Color.gray.opacity(0.3), lineWidth: 1)
                                    )
                            }
                            .buttonStyle(.plain)
                        }
                    }

                    if let city = selectedCity {
                        Button {
                            locationManager.setManualLocation(lat: city.lat, lon: city.lon)
                        } label: {
                            HStack(spacing: 8) {
                                Image(systemName: "checkmark")
                                    .font(.system(size: 14, weight: .semibold))
                                Text("Use \(city.name)")
                                    .font(.appSansSemiBold(size: 16, relativeTo: .body))
                            }
                            .foregroundStyle(.white)
                            .frame(maxWidth: .infinity)
                            .frame(height: 52)
                            .background(Color.appPrimary)
                            .clipShape(RoundedRectangle(cornerRadius: 8))
                        }
                        .buttonStyle(.plain)
                    }
                }
            }
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
