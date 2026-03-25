import SwiftUI

struct AlertSetupSheet: View {
    let productId: UUID
    let productName: String
    let currentPrice: Double

    @Environment(\.dismiss) private var dismiss
    @State private var viewModel = AlertsViewModel()
    @State private var thresholdText = ""
    @State private var alertOnPromo = false
    @State private var isSaving = false
    @State private var errorMessage: String?

    var body: some View {
        NavigationStack {
            Form {
                Section {
                    Text(productName)
                        .font(.headline)
                    Text("Current price: $\(currentPrice, specifier: "%.2f")")
                        .foregroundStyle(.secondary)
                }

                Section("Alert when price drops below") {
                    TextField("e.g. 25.00", text: $thresholdText)
                        .keyboardType(.decimalPad)
                }

                Section {
                    Toggle("Alert on any promo", isOn: $alertOnPromo)
                }

                if let error = errorMessage {
                    Section {
                        Text(error)
                            .foregroundStyle(.red)
                            .font(.caption)
                    }
                }
            }
            .navigationTitle("Set Alert")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .cancellationAction) {
                    Button("Cancel") { dismiss() }
                }
                ToolbarItem(placement: .confirmationAction) {
                    Button("Save") {
                        Task { await save() }
                    }
                    .disabled(isSaving || (thresholdText.isEmpty && !alertOnPromo))
                }
            }
        }
        .onAppear {
            thresholdText = String(format: "%.2f", currentPrice * 0.9)
        }
    }

    private func save() async {
        isSaving = true
        defer { isSaving = false }

        let threshold = Double(thresholdText)

        do {
            try await viewModel.createAlert(
                productId: productId,
                thresholdPrice: threshold,
                alertOnPromo: alertOnPromo
            )
            dismiss()
        } catch {
            errorMessage = "Failed to create alert. You may already have an active alert."
        }
    }
}
