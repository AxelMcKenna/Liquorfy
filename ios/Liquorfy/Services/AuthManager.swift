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

    // MARK: - Google

    func signInWithGoogle() async throws {
        try await supabase.auth.signInWithOAuth(provider: .google) { url in
            await UIApplication.shared.open(url)
        }
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
        guard let token = session?.accessToken else { return }

        var request = URLRequest(url: URL(string: Constants.apiBaseURL + "/user/account")!)
        request.httpMethod = "DELETE"
        request.setValue("Bearer \(token)", forHTTPHeaderField: "Authorization")

        let (_, response) = try await URLSession.shared.data(for: request)
        if let http = response as? HTTPURLResponse, !(200...299).contains(http.statusCode) {
            throw APIError.httpError(http.statusCode)
        }

        try await signOut()
    }
}
