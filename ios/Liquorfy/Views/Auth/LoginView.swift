import SwiftUI
import AuthenticationServices

struct LoginView: View {
    @Environment(AuthManager.self) private var authManager
    @Environment(\.dismiss) private var dismiss

    @State private var email = ""
    @State private var password = ""
    @State private var isLoading = false
    @State private var errorMessage: String?
    @State private var showRegister = false
    @State private var showForgotPassword = false

    private var canSubmit: Bool {
        !email.isEmpty && password.count >= 6 && !isLoading
    }

    var body: some View {
        ScrollView {
            VStack(spacing: 24) {
                VStack(spacing: 8) {
                    Text("LIQUORFY")
                        .font(.appTitle2)
                        .foregroundStyle(.appPrimary)
                    Text("Sign in to save your preferences and set price alerts")
                        .font(.subheadline)
                        .foregroundStyle(.secondary)
                        .multilineTextAlignment(.center)
                }
                .padding(.top, 32)
                .padding(.horizontal, 32)

                VStack(spacing: 12) {
                    TextField("Email", text: $email)
                        .textContentType(.emailAddress)
                        .keyboardType(.emailAddress)
                        .textInputAutocapitalization(.never)
                        .autocorrectionDisabled()
                        .textFieldStyle(.roundedBorder)

                    SecureField("Password", text: $password)
                        .textContentType(.password)
                        .textFieldStyle(.roundedBorder)

                    if let errorMessage {
                        Text(errorMessage)
                            .font(.caption)
                            .foregroundStyle(.red)
                            .frame(maxWidth: .infinity, alignment: .leading)
                    }

                    Button {
                        signIn()
                    } label: {
                        Text("Sign In")
                            .frame(maxWidth: .infinity)
                            .frame(height: 50)
                    }
                    .buttonStyle(.borderedProminent)
                    .disabled(!canSubmit)

                    Button("Forgot password?") {
                        showForgotPassword = true
                    }
                    .font(.caption)
                    .foregroundStyle(.appPrimary)
                }
                .padding(.horizontal, 32)

                HStack {
                    Rectangle().frame(height: 1).foregroundStyle(.quaternary)
                    Text("or").font(.caption).foregroundStyle(.secondary)
                    Rectangle().frame(height: 1).foregroundStyle(.quaternary)
                }
                .padding(.horizontal, 32)

                VStack(spacing: 12) {
                    // Apple Sign-In (required alongside Google per App Store Guideline 4.8)
                    SignInWithAppleButton(.signIn) { request in
                        request.requestedScopes = [.fullName, .email]
                    } onCompletion: { result in
                        switch result {
                        case .success(let authorization):
                            Task {
                                isLoading = true
                                defer { isLoading = false }
                                do {
                                    try await authManager.signInWithApple(authorization: authorization)
                                } catch {
                                    errorMessage = error.localizedDescription
                                }
                            }
                        case .failure(let error):
                            errorMessage = error.localizedDescription
                        }
                    }
                    .signInWithAppleButtonStyle(.black)
                    .frame(height: 50)
                    .clipShape(RoundedRectangle(cornerRadius: 8))

                    // Google Sign-In
                    Button {
                        Task {
                            isLoading = true
                            defer { isLoading = false }
                            do {
                                try await authManager.signInWithGoogle()
                            } catch {
                                errorMessage = error.localizedDescription
                            }
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
                }
                .padding(.horizontal, 32)

                Button {
                    showRegister = true
                } label: {
                    HStack(spacing: 4) {
                        Text("Don't have an account?")
                            .foregroundStyle(.secondary)
                        Text("Sign up")
                            .foregroundStyle(.appPrimary)
                            .fontWeight(.semibold)
                    }
                    .font(.subheadline)
                }
                .padding(.top, 8)
            }
        }
        .navigationTitle("Sign In")
        .navigationBarTitleDisplayMode(.inline)
        .onChange(of: authManager.isAuthenticated) { _, isAuthed in
            if isAuthed { dismiss() }
        }
        .sheet(isPresented: $showRegister) {
            NavigationStack { RegisterView() }
        }
        .sheet(isPresented: $showForgotPassword) {
            NavigationStack { ForgotPasswordView() }
        }
    }

    private func signIn() {
        Task {
            isLoading = true
            errorMessage = nil
            defer { isLoading = false }
            do {
                try await authManager.signInWithPassword(email: email, password: password)
            } catch {
                errorMessage = "Incorrect email or password."
            }
        }
    }
}
