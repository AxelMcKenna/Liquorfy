# Liquorfy - iOS App Store Submission Guide

## ✅ What's Already Done

Your app is now **iOS-ready** with:
- ✅ Capacitor configured and installed
- ✅ iOS platform added
- ✅ Location permissions configured
- ✅ iOS safe area handling (notch support)
- ✅ Splash screen and status bar plugins
- ✅ Production build created and synced

## 📱 Next Steps to Submit to App Store

### 1. Open the iOS Project in Xcode

```bash
cd /Users/axelmckenna/Liquorfy/web
npm run cap:open:ios
```

This will open Xcode with your iOS project.

### 2. Configure App Icons

You need to create app icons in these sizes:

**Required Sizes:**
- 1024x1024 (App Store)
- 180x180 (iPhone)
- 167x167 (iPad Pro)
- 152x152 (iPad)
- 120x120 (iPhone)
- 87x87 (iPhone)
- 80x80 (iPad)
- 76x76 (iPad)
- 60x60 (iPhone)
- 58x58 (iPhone)
- 40x40 (iPhone/iPad)
- 29x29 (iPhone/iPad)
- 20x20 (iPhone/iPad)

**How to Add Icons in Xcode:**
1. In Xcode, navigate to: `ios/App/App/Assets.xcassets/AppIcon.appiconset`
2. Drag and drop your icons into the appropriate slots
3. Or use a tool like https://www.appicon.co/ to generate all sizes

**Your App Icon Guidelines:**
- Use the green color #1fb956 as primary
- Include "Liquorfy" branding
- Keep it simple and recognizable at small sizes
- No transparency (App Store requirement)

### 3. Configure Splash Screen

Create splash screen images:

**Recommended Approach:**
Create a simple splash with the Liquorfy logo on green background (#1fb956)

**Sizes Needed:**
- 2732x2732 (Universal)
- 2048x2048 (iPad)
- 1242x2688 (iPhone)

**Location in Xcode:**
`ios/App/App/Assets.xcassets/Splash.imageset`

### 4. Update App Settings in Xcode

1. **Select the App target** in Xcode
2. **General tab:**
   - Bundle Identifier: `nz.co.liquorfy`
   - Version: `1.0.0`
   - Build: `1`
   - Deployment Target: iOS 13.0 or higher
   - Device: iPhone

3. **Signing & Capabilities:**
   - Enable "Automatically manage signing"
   - Select your Apple Developer Team
   - Or configure manual signing if preferred

4. **Info tab:**
   - All location permissions are already configured ✅
   - Review and customize if needed

### 5. Test on Real Device

**Connect iPhone via USB:**

```bash
# Build and run on device
npm run cap:run:ios
```

Or in Xcode:
1. Select your device from the device dropdown
2. Click the Play button (▶️) to build and run

**Test these features:**
- Location permission prompt
- Product search and filtering
- Comparison feature
- Maps display correctly
- Safe area handling (notch areas)

### 6. Create App Store Connect Listing

**Prerequisites:**
- Apple Developer Account ($99/year)
- https://developer.apple.com/

**Steps:**
1. Go to https://appstoreconnect.apple.com/
2. Click "My Apps" → "+" → "New App"
3. Fill in:
   - **Platform:** iOS
   - **Name:** Liquorfy
   - **Primary Language:** English (NZ)
   - **Bundle ID:** nz.co.liquorfy
   - **SKU:** liquorfy-nz-001
   - **User Access:** Full Access

### 7. Prepare App Store Metadata

**App Information:**
- **Name:** Liquorfy
- **Subtitle:** Compare Liquor Prices in NZ
- **Category:** Shopping
- **Age Rating:** 17+ (Alcohol content)

**Description:**
```
Find the best liquor prices across New Zealand's top retailers. Liquorfy helps you compare prices for beer, wine, and spirits from stores near you.

FEATURES:
• Compare prices across 10+ major retailers
• Find deals and promotions near you
• Sort by distance, price, or best value
• Side-by-side product comparison
• Real-time pricing updates
• Store locations on map

RETAILERS INCLUDED:
Super Liquor, Liquorland, Bottle-O, Countdown, New World, PAK'nSAVE, Liquor Centre, Glengarry, and more.

Save money on your favorite drinks. Download Liquorfy today!

Note: Must be 18+ to purchase alcohol. Drink responsibly.
```

**Keywords:**
```
liquor, beer, wine, spirits, alcohol, prices, compare, deals, nz, new zealand, shopping
```

**Screenshots Required:**
You need to provide screenshots:
- **6.7" iPhone (iPhone 15 Pro Max):** 3-10 screenshots
- **5.5" iPhone (optional but recommended):** 3-10 screenshots

**Screenshot Tips:**
- Capture these screens:
  1. Landing page with search
  2. Product grid with deals
  3. Product detail page
  4. Comparison tray
  5. Map view with stores
- Use device with good location and data
- Remove any personal info
- Show real deals and products

### 8. Privacy Policy & Support

**Required URLs:**

1. **Privacy Policy URL:**
   - Host at: https://liquorfy.co.nz/privacy
   - Must explain:
     - Location data usage
     - Data storage
     - Third-party services (if any)

2. **Support URL:**
   - Example: https://liquorfy.co.nz/support
   - Or email: support@liquorfy.co.nz

3. **App Privacy Details in App Store Connect:**
   - **Data Types Collected:**
     - ✅ Location (Precise Location)
       - Used for: Product Personalization, App Functionality
       - Not linked to user identity
       - Not used for tracking

### 9. Build and Archive for App Store

**In Xcode:**

1. **Select "Any iOS Device (arm64)" from device dropdown**
2. **Product → Archive**
3. Wait for archive to complete
4. **Distribute App:**
   - Select "App Store Connect"
   - Upload
   - Select automatic signing (or manual if configured)

### 10. Submit for Review

**In App Store Connect:**

1. Select your app version
2. Add all metadata (description, screenshots, etc.)
3. Select your uploaded build
4. **Content Rights:** Check "Your app uses the Apple Maps service"
5. **Export Compliance:** No (uses standard encryption only)
6. **Advertising Identifier:** No
7. **Submit for Review**

**Review Notes for Apple:**
```
Liquorfy is a price comparison app for alcoholic beverages in New Zealand.

TESTING:
- Location permission is required to show nearby stores
- Grant location access when prompted
- Test with Wellington, NZ location: -41.2865, 174.7762
- Products and prices are live from New Zealand retailers

Note: This is an informational tool only. We don't sell alcohol.
```

### 11. After Submission

**Timeline:**
- Review typically takes 24-48 hours
- You'll receive email updates

**If Rejected:**
- Read rejection reason carefully
- Make requested changes
- Resubmit

**Common Rejection Reasons:**
- Missing age gate (you may need to add 18+ verification screen)
- Incomplete metadata
- App crashes during review
- Privacy policy issues

## 🔄 Updating Your App

**When you make changes:**

```bash
# 1. Make your code changes
# 2. Build and sync
npm run cap:sync

# 3. Open Xcode
npm run cap:open:ios

# 4. Update version/build number in Xcode
# 5. Archive and upload new build
# 6. Submit update in App Store Connect
```

## 🛠️ Development Commands

```bash
# Build web app
npm run build

# Sync changes to iOS
npx cap sync ios

# Open in Xcode
npm run cap:open:ios

# Build and open (combined)
npm run cap:run:ios

# Copy to Android (bonus)
npx cap add android
npm run cap:run:android
```

## 📋 Checklist Before Submission

- [ ] App icons added (all sizes)
- [ ] Splash screen configured
- [ ] Bundle ID set: nz.co.liquorfy
- [ ] Version and build number set
- [ ] Tested on real iPhone device
- [ ] Location permission works
- [ ] All features tested
- [ ] Screenshots captured
- [ ] Privacy policy created and hosted
- [ ] Support URL configured
- [ ] App Store listing completed
- [ ] App archived and uploaded
- [ ] Submitted for review

## 🚨 Important Notes

1. **Age Restriction:** Consider adding an age gate (18+) on first launch to avoid rejection
2. **Responsible Drinking:** Include disclaimers in app and App Store description
3. **API URL:** Make sure your production API URL is set in `.env.production`
4. **Analytics:** Consider adding App Store analytics

## 🎉 App Store Optimization (ASO)

**After Approval:**
- Monitor reviews and respond
- Track download analytics
- Optimize keywords based on performance
- Update screenshots seasonally
- A/B test app icon and screenshots

## 💰 Pricing

Your app is currently configured as **Free**.

To monetize:
- Add in-app purchases (IAP)
- Implement subscription model
- Or change to paid app in App Store Connect

## 📞 Need Help?

- Capacitor Docs: https://capacitorjs.com/docs/ios
- App Store Review Guidelines: https://developer.apple.com/app-store/review/guidelines/
- Apple Developer Forums: https://developer.apple.com/forums/

---

**Your app is ready for the App Store! 🚀**

Next step: `npm run cap:open:ios` and follow the guide above.
