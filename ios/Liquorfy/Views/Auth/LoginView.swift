import SwiftUI
import AuthenticationServices

struct LoginView: View {
    @Environment(AuthManager.self) private var authManager
    @Environment(\.dismiss) private var dismiss
    @State private var isLoading = false

    var body: some View {
        VStack(spacing: 24) {
            Spacer()

            VStack(spacing: 8) {
                Text("LIQUORFY")
                    .font(.appTitle2)
                    .foregroundStyle(.appPrimary)
                Text("Sign in to save your preferences and set price alerts")
                    .font(.subheadline)
                    .foregroundStyle(.secondary)
                    .multilineTextAlignment(.center)
            }
            .padding(.horizontal, 32)

            VStack(spacing: 12) {
                // Google Sign-In
                Button {
                    Task {
                        isLoading = true
                        defer { isLoading = false }
                        try? await authManager.signInWithGoogle()
                    }
                } label: {
                    HStack {
                        Image(systemName: "globe")
                        Text("Continue with Google")
                    }
                    .frame(maxWidth: .infinity)
                    .frame(height: 50)
                }
                .buttonStyle(.bordered)
                .disabled(isLoading)

                // Apple Sign-In
                SignInWithAppleButton(.signIn) { request in
                    request.requestedScopes = [.email, .fullName]
                } onCompletion: { result in
                    switch result {
                    case .success(let authorization):
                        Task {
                            try? await authManager.signInWithApple(authorization: authorization)
                        }
                    case .failure:
                        break
                    }
                }
                .signInWithAppleButtonStyle(.black)
                .frame(height: 50)
                .cornerRadius(8)
            }
            .padding(.horizontal, 32)

            Spacer()

            NavigationLink(destination: Text("Privacy Policy")) {
                Text("Privacy Policy")
                    .font(.caption)
                    .foregroundStyle(.secondary)
            }
            .padding(.bottom, 16)
        }
    }
}
