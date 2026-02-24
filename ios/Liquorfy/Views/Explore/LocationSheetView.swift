import SwiftUI

struct LocationSheetView: View {
    var onLocationChanged: () -> Void

    @Environment(LocationManager.self) private var locationManager
    @Environment(\.dismiss) private var dismiss

    @State private var tempRadius: Double = Constants.Radius.default
    @State private var selectedCity: NZCity?

    var body: some View {
        NavigationStack {
            ScrollView {
                VStack(spacing: 24) {
                    // Current location info
                    if locationManager.isLocationSet, let loc = locationManager.location {
                        VStack(spacing: 8) {
                            HStack(spacing: 8) {
                                Image(systemName: "checkmark.circle.fill")
                                    .foregroundStyle(Color.appPrimary)
                                Text("Location Set")
                                    .font(.appSansSemiBold(size: 16, relativeTo: .body))
                            }

                            Text(String(format: "%.4f, %.4f", loc.latitude, loc.longitude))
                                .font(.appCaption)
                                .foregroundStyle(.secondary)
                        }
                        .padding(16)
                        .frame(maxWidth: .infinity)
                        .background(Color.appPrimary.opacity(0.05))
                        .overlay(
                            RoundedRectangle(cornerRadius: 8)
                                .stroke(Color.appPrimary.opacity(0.2), lineWidth: 1)
                        )
                        .clipShape(RoundedRectangle(cornerRadius: 8))
                    }

                    // Radius slider
                    VStack(alignment: .leading, spacing: 8) {
                        HStack {
                            Text("Search Radius")
                                .font(.appSansMedium(size: 14, relativeTo: .subheadline))
                            Spacer()
                            Text("\(Int(tempRadius)) km")
                                .font(.appSansSemiBold(size: 14, relativeTo: .subheadline))
                                .foregroundStyle(Color.appPrimary)
                        }

                        Slider(
                            value: $tempRadius,
                            in: Constants.Radius.min...Constants.Radius.max,
                            step: 1
                        )
                        .tint(Color.appPrimary)

                        HStack {
                            Text("\(Int(Constants.Radius.min)) km")
                                .font(.appCaption)
                                .foregroundStyle(.secondary)
                            Spacer()
                            Text("\(Int(Constants.Radius.max)) km")
                                .font(.appCaption)
                                .foregroundStyle(.secondary)
                        }
                    }
                    .padding(16)
                    .background(Color.appTertiaryBackground)
                    .clipShape(RoundedRectangle(cornerRadius: 8))

                    // Use My Location button
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
                            Text(locationManager.isLoading ? "Getting location..." : "Use My Location")
                                .font(.appSansSemiBold(size: 16, relativeTo: .body))
                        }
                        .foregroundStyle(.white)
                        .frame(maxWidth: .infinity)
                        .frame(height: 48)
                        .background(Color.appPrimary)
                        .clipShape(RoundedRectangle(cornerRadius: 8))
                    }
                    .buttonStyle(.plain)
                    .disabled(locationManager.isLoading)

                    if let error = locationManager.error {
                        Text(error)
                            .font(.appCaption)
                            .foregroundStyle(.red)
                            .multilineTextAlignment(.center)
                    }

                    // Manual city selection
                    VStack(alignment: .leading, spacing: 12) {
                        Text("Or select a city")
                            .font(.appSansMedium(size: 14, relativeTo: .subheadline))

                        LazyVGrid(columns: [GridItem(.flexible()), GridItem(.flexible())], spacing: 8) {
                            ForEach(NZCity.allCases) { city in
                                Button {
                                    selectedCity = city
                                    locationManager.setManualLocation(lat: city.lat, lon: city.lon)
                                } label: {
                                    Text(city.name)
                                        .font(.appCardBody)
                                        .frame(maxWidth: .infinity)
                                        .padding(.vertical, 10)
                                        .background(selectedCity == city ? Color.appPrimary : .white)
                                        .foregroundStyle(selectedCity == city ? .white : .primary)
                                        .clipShape(RoundedRectangle(cornerRadius: 8))
                                        .overlay(
                                            RoundedRectangle(cornerRadius: 8)
                                                .stroke(selectedCity == city ? Color.clear : Color.black.opacity(0.1), lineWidth: 1)
                                        )
                                }
                                .buttonStyle(.plain)
                            }
                        }
                    }
                }
                .padding(24)
            }
            .background(.white)
            .navigationTitle("Location")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .topBarLeading) {
                    Button {
                        dismiss()
                    } label: {
                        Image(systemName: "xmark")
                            .font(.system(size: 14, weight: .medium))
                            .foregroundStyle(.secondary)
                    }
                }
                ToolbarItem(placement: .topBarTrailing) {
                    Button {
                        locationManager.setRadius(tempRadius)
                        dismiss()
                        onLocationChanged()
                    } label: {
                        Text("Done")
                            .font(.appSansSemiBold(size: 15, relativeTo: .body))
                            .foregroundStyle(.white)
                            .padding(.horizontal, 16)
                            .padding(.vertical, 8)
                            .background(Color.appPrimary)
                            .clipShape(RoundedRectangle(cornerRadius: 6))
                    }
                    .buttonStyle(.plain)
                }
            }
        }
        .onAppear {
            tempRadius = locationManager.radiusKm
        }
    }
}

#Preview {
    LocationSheetView(onLocationChanged: {})
        .environment(LocationManager())
}
