# Liquorfy Mobile App - Quick Start

## 🚀 Your App is iOS-Ready!

Liquorfy is now configured to deploy to the Apple App Store using **Capacitor**.

## Quick Commands

```bash
# Open iOS project in Xcode
npm run cap:open:ios

# Build web + sync to iOS
npm run cap:sync

# Build, sync, and open Xcode (all-in-one)
npm run cap:run:ios
```

## What's Configured

✅ **Capacitor Installed** - Native wrapper for your React app
✅ **iOS Platform Added** - Xcode project created at `ios/`
✅ **Location Permission** - Required descriptions added to Info.plist
✅ **Safe Area Support** - Handles iPhone notches/home indicators
✅ **Native Plugins:**
  - Geolocation - Access device location
  - Splash Screen - Native splash screen on launch
  - Status Bar - Control status bar appearance

## File Structure

```
web/
├── ios/                          # iOS native project (Xcode)
│   └── App/
│       ├── App.xcodeproj         # Xcode project file
│       └── App/
│           ├── Info.plist        # iOS app configuration
│           ├── Assets.xcassets/  # App icons & splash screens
│           └── public/           # Your built web app
├── capacitor.config.ts           # Capacitor configuration
├── APP_STORE_GUIDE.md           # Complete submission guide
└── MOBILE_README.md             # This file
```

## Development Workflow

### 1. Make Web Changes
Edit your React components as normal in `src/`

### 2. Test in Browser
```bash
npm run dev
```

### 3. Test on iOS
```bash
# Build web app and sync to iOS
npm run cap:sync

# Open Xcode and run on simulator or device
npm run cap:open:ios
```

### 4. Before Each iOS Test
Always build + sync after making changes:
```bash
npm run build && npx cap sync ios
```

## App Store Submission

**See the complete guide:** `APP_STORE_GUIDE.md`
**SPM container notes:** `ios/CapApp-SPM.md`

**Quick checklist:**
1. Create app icons (use https://www.appicon.co/)
2. Configure bundle ID in Xcode: `nz.co.liquorfy`
3. Test on real iPhone device
4. Archive and upload to App Store Connect
5. Fill in App Store metadata
6. Submit for review

## Native Features

### Location Access
```typescript
// Already configured! Your existing location code works
import { Geolocation } from '@capacitor/geolocation';

const position = await Geolocation.getCurrentPosition();
```

### Status Bar
```typescript
import { StatusBar, Style } from '@capacitor/status-bar';

// Light content for dark backgrounds
await StatusBar.setStyle({ style: Style.Light });

// Dark content for light backgrounds
await StatusBar.setStyle({ style: Style.Dark });
```

### Splash Screen
```typescript
import { SplashScreen } from '@capacitor/splash-screen';

// Hide splash screen
await SplashScreen.hide();

// Show splash screen
await SplashScreen.show();
```

## Android Support

Want Android too? Easy:

```bash
# Add Android platform
npx cap add android

# Open in Android Studio
npm run cap:open:android
```

All your code works on both platforms!

## Troubleshooting

### Build Fails
```bash
# Clean and rebuild
rm -rf ios/App/App/public
npm run build
npx cap sync ios
```

### Location Not Working
- Check Info.plist has location descriptions ✅ (already configured)
- Test on real device (simulator location is limited)
- Grant permission when prompted

### Xcode Errors
- Make sure you have Xcode 14+ installed
- Open Xcode and install any suggested components
- Select a development team in Signing & Capabilities

### Web Changes Not Showing
- Always run `npm run build && npx cap sync` after changes
- Clean and rebuild in Xcode if needed

## Environment Variables

Create `.env.production` for production API:

```env
VITE_API_URL=https://api.liquorfy.co.nz
```

Capacitor will use your production build with this URL.

## App Configuration

Edit `capacitor.config.ts` to change:
- App ID: `appId: 'nz.co.liquorfy'`
- App Name: `appName: 'Liquorfy'`
- Splash screen settings
- Plugin configurations

## Testing Checklist

Before submitting to App Store, test:

- [ ] Location permission prompt appears
- [ ] Location updates properly
- [ ] All screens render correctly (no overflow)
- [ ] Safe areas respected (no content behind notch)
- [ ] Product search works
- [ ] Map displays correctly
- [ ] Comparison feature works
- [ ] External links open in Safari
- [ ] App doesn't crash on any screen
- [ ] Works on both iPhone and iPad

## Production Checklist

- [ ] Set production API URL in `.env.production`
- [ ] Update version in `package.json`
- [ ] Update version and build in Xcode
- [ ] Test on real device
- [ ] Run production build: `npm run build`
- [ ] Sync to iOS: `npx cap sync ios`
- [ ] Archive in Xcode
- [ ] Upload to App Store Connect

## Resources

- **Capacitor Docs:** https://capacitorjs.com/docs
- **iOS Guide:** https://capacitorjs.com/docs/ios
- **App Store Guidelines:** https://developer.apple.com/app-store/review/guidelines/
- **Your Submission Guide:** `APP_STORE_GUIDE.md`

## Support

Questions about:
- **Capacitor setup:** Check Capacitor docs
- **iOS development:** Check Apple Developer docs
- **App Store submission:** See `APP_STORE_GUIDE.md`

---

**Ready to deploy?**
👉 Open `APP_STORE_GUIDE.md` for the complete submission process.

**Want to test right now?**
👉 Run `npm run cap:open:ios` and click the play button in Xcode!
