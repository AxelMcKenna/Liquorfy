import Foundation
import AuthenticationServices
import Supabase

@Observable
final class AuthManager {
    var session: Session?
    var user: User?
    var isAuthenticated: Bool { session != nil }
    var isLoading = true

    init() {
        Task { await loadSession() }
    }

    // MARK: - Session

    private func loadSession() async {
        do {
            session = try await supabase.auth.session
            user = session?.user
        } catch {
            session = nil
            user = nil
        }
        isLoading = false

        // Listen for auth state changes
        Task {
            for await (_, session) in supabase.auth.authStateChanges {
                await MainActor.run {
                    self.session = session
                    self.user = session?.user
                }
            }
        }
    }

    // MARK: - Email / Password

    func signInWithPassword(email: String, password: String) async throws {
        try await supabase.auth.signIn(email: email, password: password)
    }

    /// Returns true when the session is active immediately (email confirmation disabled),
    /// false when a confirmation email was sent and the user must verify before signing in.
    @discardableResult
    func signUp(email: String, password: String, name: String?) async throws -> Bool {
        let response = try await supabase.auth.signUp(
            email: email,
            password: password,
            data: name.map { ["full_name": AnyJSON.string($0)] }
        )
        return response.session != nil
    }

    func sendPasswordReset(email: String) async throws {
        try await supabase.auth.resetPasswordForEmail(email)
    }

    // MARK: - Google

    func signInWithGoogle() async throws {
        // Uses Supabase's built-in ASWebAuthenticationSession flow. The callback
        // scheme below must be declared in Info.plist and allow-listed in the
        // Supabase dashboard's redirect URLs.
        try await supabase.auth.signInWithOAuth(
            provider: .google,
            redirectTo: URL(string: "nz.co.liquorfy://auth/callback")
        )
    }

    // MARK: - Apple

    func signInWithApple(authorization: ASAuthorization) async throws {
        guard let credential = authorization.credential as? ASAuthorizationAppleIDCredential,
              let identityToken = credential.identityToken,
              let tokenString = String(data: identityToken, encoding: .utf8)
        else {
            return
        }

        try await supabase.auth.signInWithIdToken(
            credentials: .init(
                provider: .apple,
                idToken: tokenString
            )
        )
    }

    // MARK: - Sign Out

    func signOut() async throws {
        try await supabase.auth.signOut()
        session = nil
        user = nil
    }

    // MARK: - Delete Account

    func deleteAccount() async throws {
        guard session?.accessToken != nil else { return }
        try await APIClient.shared.deleteAccount()
        try await signOut()
    }
}
