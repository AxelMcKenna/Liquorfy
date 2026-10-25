# App Store submission checklist - Liquorfy iOS 1.0

Remaining steps to get `ios/` into App Review. Listing copy, privacy labels and
reviewer notes live in [APP_STORE_LISTING.md](APP_STORE_LISTING.md).

## Already done in code

- [x] Sign in with Apple entitlement (`ios/Liquorfy/Liquorfy.entitlements`)
- [x] Export compliance declared (`ITSAppUsesNonExemptEncryption = false`)
- [x] OAuth callback scheme `nz.co.liquorfy` registered in `Info.plist`
- [x] Privacy manifest covers location, email, name, user ID
- [x] Account deletion shows progress and surfaces failures
- [x] First-launch 18+ age gate
- [x] iPhone-only (`TARGETED_DEVICE_FAMILY = 1`)
- [x] Development team set (`S5VV6HB4R5`)
- [x] Release build compiles; 38 unit tests pass on the iPhone 17 Pro Max simulator

## 1. Apple Developer account (blocker)

- [ ] Accept the latest Program License Agreement at
      https://developer.apple.com/account. Until this is done, archiving fails with
      `PLA Update available` and Xcode can't create the App ID or provisioning profile.

## 2. Signing and archive

- [ ] Open `ios/Liquorfy.xcodeproj` → Liquorfy target → Signing & Capabilities.
      Confirm the team is selected and **Sign in with Apple** appears as a capability.
      Automatic signing registers the `nz.co.liquorfy` App ID with that capability.
- [ ] Archive: Product → Archive (destination "Any iOS Device"), or from the CLI:

  ```sh
  cd ios
  xcodebuild archive -project Liquorfy.xcodeproj -scheme Liquorfy \
    -configuration Release -destination 'generic/platform=iOS' \
    -archivePath build/Liquorfy.xcarchive -allowProvisioningUpdates
  ```

- [ ] Window → Organizer → Distribute App → App Store Connect → Upload.
- [ ] Bump `CURRENT_PROJECT_VERSION` before every re-upload (App Store Connect
      rejects duplicate build numbers). `MARKETING_VERSION` stays `1.0` for launch.

## 3. Supabase auth config

In the Supabase dashboard for project `udrbkdygzhbyktlljkwp` (Authentication):

- [ ] URL Configuration → Redirect URLs: add `nz.co.liquorfy://auth/callback`
      (required for Google sign-in on iOS).
- [ ] Providers → Apple: enable it and add `nz.co.liquorfy` to the authorized
      client IDs (the iOS app sends a native identity token, so the bundle ID is
      the client ID).
- [ ] Test both on a real device after the profile from step 2 exists:
      Apple sign-in, Google sign-in, email sign-up, Delete Account.

## 4. Demo account for App Review

- [ ] Create a dedicated email/password account (e.g. a `+appreview` alias of the
      support inbox), confirm it, and create one price alert on it so the reviewer
      sees populated data.
- [ ] Do not commit the credentials; enter them only in App Store Connect →
      App Review Information.

## 5. App Store Connect

- [ ] Create the app record: My Apps → + → New App, platform iOS, bundle ID
      `nz.co.liquorfy`, SKU `liquorfy-ios`.
- [ ] Fill in name, subtitle, promotional text, description, keywords, URLs and
      categories from APP_STORE_LISTING.md.
- [ ] Pricing and Availability: Free, **New Zealand only**.
- [ ] Age rating questionnaire: Alcohol, Tobacco, or Drug Use or References =
      Frequent; everything else None → 18+.
- [ ] App Privacy: enter the nutrition label from APP_STORE_LISTING.md. It must
      match `ios/Liquorfy/PrivacyInfo.xcprivacy`.
- [ ] App Review Information: demo account, contact details, reviewer notes.
- [ ] Select the uploaded build once processing finishes (usually 10-30 min).

## 6. Screenshots

iPhone 6.9" (1320 × 2868) only. Capture on the iPhone 17 Pro Max simulator with a
clean status bar:

```sh
xcrun simctl status_bar booted override --time 9:41 --batteryState charged \
  --batteryLevel 100 --cellularBars 4 --wifiBars 3
xcrun simctl location booted set -36.8485,174.7633   # central Auckland
xcrun simctl io booted screenshot 01-landing.png
```

- [x] Landing with top deals
- [ ] Search results for a popular product
- [ ] Product detail with cross-store comparison
- [ ] Store map with nearby stores
- [ ] Price history / alert setup

## 7. Before you press Submit

- [ ] Smoke test the uploaded build through TestFlight on a real iPhone:
      age gate → deny location → deals still load → pick a location manually →
      search → product detail → View at Store → sign in → set alert → delete account.
- [ ] Privacy and support pages load: https://www.liquorfy.co.nz/privacy,
      https://www.liquorfy.co.nz/support
- [ ] Submit for Review.

## Known non-blocking polish

- Landing page status bar text is dark on the dark green header; set a light
  status bar style for that screen.
- First deals load can take 8+ seconds when the API is cold. Reviewers judge
  perceived performance, so consider warming the API or caching the top-deals
  response before submitting.

## Common rejection reasons to watch for

- **2.1 App completeness**: crashes, empty screens or placeholder content during
  review. Make sure the API is up the whole time the app is in review.
- **4.8 Login services**: Sign in with Apple must work whenever Google sign-in is
  offered.
- **5.1.1(v) Account deletion**: must work end to end from inside the app.
- **5.1.2 Data use**: the privacy label must match what the app collects.
- **1.4.3 / 5.3 Alcohol**: no promotion of excessive drinking; keep the
  responsible-drinking message and the 18+ rating.
