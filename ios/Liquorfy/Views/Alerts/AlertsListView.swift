import SwiftUI

struct AlertsListView: View {
    @State private var viewModel = AlertsViewModel()

    var body: some View {
        Group {
            if viewModel.isLoading {
                ProgressView()
                    .frame(maxWidth: .infinity, maxHeight: .infinity)
            } else if viewModel.alerts.isEmpty {
                ContentUnavailableView(
                    "No Alerts",
                    systemImage: "bell",
                    description: Text("Tap the bell icon on any product to get notified when prices drop.")
                )
            } else {
                List {
                    ForEach(viewModel.alerts) { alert in
                        VStack(alignment: .leading, spacing: 4) {
                            Text(alert.productName ?? "Unknown product")
                                .font(.headline)

                            HStack(spacing: 12) {
                                if let threshold = alert.thresholdPrice {
                                    Text("Below $\(threshold, specifier: "%.2f")")
                                        .font(.caption)
                                        .foregroundStyle(.secondary)
                                }
                                if alert.alertOnPromo {
                                    Text("On promo")
                                        .font(.caption)
                                        .foregroundStyle(.secondary)
                                }
                                if !alert.active {
                                    Text("Paused")
                                        .font(.caption)
                                        .foregroundStyle(.orange)
                                }
                            }
                        }
                        .swipeActions(edge: .trailing) {
                            Button(role: .destructive) {
                                Task { try? await viewModel.deleteAlert(id: alert.id) }
                            } label: {
                                Label("Delete", systemImage: "trash")
                            }
                        }
                    }
                }
            }
        }
        .navigationTitle("My Alerts")
        .task { await viewModel.fetchAlerts() }
    }
}
