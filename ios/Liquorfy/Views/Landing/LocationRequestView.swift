import SwiftUI

struct LocationRequestView: View {
    @Environment(LocationManager.self) private var locationManager

    @State private var showManualEntry = false
    @State private var selectedCity: NZCity?

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
                    Label("Use My Location", systemImage: "location.fill")
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

            Button {
                withAnimation { showManualEntry.toggle() }
            } label: {
                Text(showManualEntry ? "Hide manual entry" : "Or set location manually")
                    .font(.caption)
                    .foregroundStyle(.secondary)
            }

            if showManualEntry {
                VStack(spacing: 12) {
                    Text("Select a city")
                        .font(.subheadline)
                        .fontWeight(.medium)

                    LazyVGrid(columns: [GridItem(.flexible()), GridItem(.flexible())], spacing: 8) {
                        ForEach(NZCity.allCases) { city in
                            Button {
                                selectedCity = city
                                locationManager.setManualLocation(lat: city.lat, lon: city.lon)
                            } label: {
                                Text(city.name)
                                    .font(.subheadline)
                                    .frame(maxWidth: .infinity)
                                    .padding(.vertical, 10)
                                    .background(selectedCity == city ? Color.appPrimary : Color.appCardBackground)
                                    .foregroundStyle(selectedCity == city ? .white : .primary)
                                    .clipShape(RoundedRectangle(cornerRadius: 8))
                            }
                        }
                    }
                }
                .padding(.top, 4)
            }
        }
        .padding(.vertical, 32)
        .padding(.horizontal)
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
