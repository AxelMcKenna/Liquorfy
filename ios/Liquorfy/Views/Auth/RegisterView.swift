import SwiftUI

struct RegisterView: View {
    @Environment(AuthManager.self) private var authManager
    @Environment(\.dismiss) private var dismiss

    @State private var name = ""
    @State private var email = ""
    @State private var password = ""
    @State private var isLoading = false
    @State private var errorMessage: String?
    @State private var confirmationMessage: String?

    private var canSubmit: Bool {
        !email.isEmpty && password.count >= 6 && !isLoading
    }

    var body: some View {
        ScrollView {
            VStack(spacing: 24) {
                VStack(spacing: 8) {
                    Text("Create account")
                        .font(.appTitle3)
                    Text("Save favourites, set price alerts and sync your preferences.")
                        .font(.subheadline)
                        .foregroundStyle(.secondary)
                        .multilineTextAlignment(.center)
                }
                .padding(.top, 24)
                .padding(.horizontal, 32)

                VStack(spacing: 12) {
                    TextField("Name (optional)", text: $name)
                        .textContentType(.name)
                        .textFieldStyle(.roundedBorder)

                    TextField("Email", text: $email)
                        .textContentType(.emailAddress)
                        .keyboardType(.emailAddress)
                        .textInputAutocapitalization(.never)
                        .autocorrectionDisabled()
                        .textFieldStyle(.roundedBorder)

                    SecureField("Password (min 6 characters)", text: $password)
                        .textContentType(.newPassword)
                        .textFieldStyle(.roundedBorder)

                    if let errorMessage {
                        Text(errorMessage)
                            .font(.caption)
                            .foregroundStyle(.red)
                            .frame(maxWidth: .infinity, alignment: .leading)
                    }

                    if let confirmationMessage {
                        Text(confirmationMessage)
                            .font(.caption)
                            .foregroundStyle(.appPrimary)
                            .frame(maxWidth: .infinity, alignment: .leading)
                    }

                    Button {
                        register()
                    } label: {
                        Text("Sign Up")
                            .frame(maxWidth: .infinity)
                            .frame(height: 50)
                    }
                    .buttonStyle(.borderedProminent)
                    .disabled(!canSubmit)
                }
                .padding(.horizontal, 32)
            }
        }
        .navigationTitle("Sign Up")
        .navigationBarTitleDisplayMode(.inline)
        .toolbar {
            ToolbarItem(placement: .cancellationAction) {
                Button("Cancel") { dismiss() }
            }
        }
        .onChange(of: authManager.isAuthenticated) { _, isAuthed in
            if isAuthed { dismiss() }
        }
    }

    private func register() {
        Task {
            isLoading = true
            errorMessage = nil
            confirmationMessage = nil
            defer { isLoading = false }
            do {
                let active = try await authManager.signUp(
                    email: email,
                    password: password,
                    name: name.isEmpty ? nil : name
                )
                if !active {
                    confirmationMessage = "Check your inbox to confirm your email, then sign in."
                }
            } catch {
                errorMessage = error.localizedDescription
            }
        }
    }
}
