import SwiftUI

struct AccountView: View {
    @Environment(AuthManager.self) private var authManager
    @State private var showDeleteConfirm = false
    @State private var isDeleting = false
    @State private var deleteError: String?

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

                Button(role: .destructive) {
                    showDeleteConfirm = true
                } label: {
                    if isDeleting {
                        HStack {
                            Text("Deleting Account…")
                            Spacer()
                            ProgressView()
                        }
                    } else {
                        Text("Delete Account")
                    }
                }
                .disabled(isDeleting)
            }
        }
        .navigationTitle("Account")
        .alert("Delete Account?", isPresented: $showDeleteConfirm) {
            Button("Cancel", role: .cancel) {}
            Button("Delete", role: .destructive) {
                Task {
                    isDeleting = true
                    defer { isDeleting = false }
                    do {
                        try await authManager.deleteAccount()
                    } catch {
                        deleteError = "We couldn't delete your account. Check your connection and try again, or contact liquorfy@gmail.com."
                    }
                }
            }
        } message: {
            Text("This will permanently delete your account and all associated data. This cannot be undone.")
        }
        .alert("Account Not Deleted", isPresented: Binding(
            get: { deleteError != nil },
            set: { if !$0 { deleteError = nil } }
        )) {
            Button("OK", role: .cancel) {}
        } message: {
            Text(deleteError ?? "")
        }
    }
}
