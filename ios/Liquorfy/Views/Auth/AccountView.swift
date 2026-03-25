import SwiftUI

struct AccountView: View {
    @Environment(AuthManager.self) private var authManager
    @State private var showDeleteConfirm = false
    @State private var isDeleting = false

    var body: some View {
        List {
            Section("Account") {
                if let email = authManager.user?.email {
                    LabeledContent("Email", value: email)
                }
            }

            Section("Price Alerts") {
                NavigationLink("My Alerts") {
                    AlertsListView()
                }
            }

            Section {
                Button("Sign Out") {
                    Task { try? await authManager.signOut() }
                }

                Button("Delete Account", role: .destructive) {
                    showDeleteConfirm = true
                }
            }
        }
        .navigationTitle("Account")
        .alert("Delete Account?", isPresented: $showDeleteConfirm) {
            Button("Cancel", role: .cancel) {}
            Button("Delete", role: .destructive) {
                Task {
                    isDeleting = true
                    defer { isDeleting = false }
                    try? await authManager.deleteAccount()
                }
            }
        } message: {
            Text("This will permanently delete your account and all associated data. This cannot be undone.")
        }
    }
}
