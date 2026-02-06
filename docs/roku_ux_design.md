# IPTV Roku App UX Design (SceneGraph)

This document defines the UX structure, SceneGraph hierarchy, navigation rules, component breakdown, and state logic for the IPTV Roku app. It is intentionally focused on UX flow and SceneGraph architecture (no backend implementation details).

## 1) SceneGraph Screen Hierarchy (Text Diagram)

```
App
└── MainScene (Scene)
    ├── SplashView (Group)
    │   ├── AppLogo (Poster/Label)
    │   ├── Spinner (BusySpinner)
    │   └── LoadingText (Label)
    ├── AuthFlow (Group)
    │   └── LoginScene (Scene)
    │       ├── LoginForm (Group)
    │       │   ├── UsernameField (TextEditBox)
    │       │   ├── PasswordField (TextEditBox)
    │       │   ├── DeviceCodeToggle (Toggle)
    │       │   └── RememberMeToggle (Toggle)
    │       ├── AuthSpinner (BusySpinner)
    │       └── AuthError (Label)
    ├── HomeScene (Scene)
    │   ├── TopBar (Group)
    │   │   ├── TabBar (MarkupList or RowList)
    │   │   ├── SearchInput (TextEditBox)
    │   │   ├── FilterSelector (Button/LabelList)
    │   │   └── SortSelector (Button/LabelList)
    │   ├── ContentPane (Group)
    │   │   ├── LiveTab (Group)
    │   │   │   ├── FavoritesRow (RowList)
    │   │   │   └── CategoryRows (RowList)
    │   │   ├── MoviesTab (Group)
    │   │   │   └── CategoryRows (RowList)
    │   │   ├── SeriesTab (Group)
    │   │   │   └── CategoryRows (RowList)
    │   │   ├── StatusTab (Group)
    │   │   │   └── StatusList (LabelList)
    │   │   └── RefreshTab (Group)
    │   │       └── RefreshButton (Button)
    │   ├── DetailView (Group)
    │   │   ├── Poster (Poster)
    │   │   ├── Title (Label)
    │   │   ├── Description (Label)
    │   │   ├── MetaRow (Group)
    │   │   │   ├── Duration (Label)
    │   │   │   ├── GenreTags (LabelList)
    │   │   │   └── Rating (Label)
    │   │   ├── PrimaryActions (Group)
    │   │   │   ├── PlayButton (Button)
    │   │   │   └── FavoriteButton (Button)
    │   │   ├── LiveMeta (Group)
    │   │   │   ├── ChannelLogo (Poster)
    │   │   │   └── CurrentProgram (Label)
    │   │   └── SeriesMeta (Group)
    │   │       ├── SeasonSelector (LabelList)
    │   │       └── EpisodeList (MarkupList)
    │   └── GlobalOverlays (Group)
    │       ├── RefreshModal (Dialog)
    │       ├── Toast (Label)
    │       └── ErrorDialog (Dialog)
    └── PlaybackScene (Scene)
        └── Video (Video)
```

## 2) Component Breakdown (XML Components)

### Scenes
- **MainScene.xml**: Root scene, hosts Splash, Auth, Home, and Playback routing containers.
- **LoginScene.xml**: Login form with device code option, status labels, and spinner.
- **HomeScene.xml**: Tab navigation + content grid container + detail view + overlays.
- **PlaybackScene.xml**: Video playback container with minimal chrome (separate scene for fast entry/exit).

### Reusable Components
- **TabBar.xml**: Horizontal or vertical tabs with focus styles and focus-change events.
- **RowShelf.xml**: Horizontal content shelf with label + RowList for items.
- **ContentGrid.xml**: Vertical stack of RowShelf components with shared focus rules.
- **DetailView.xml**: Base detail panel with optional Live/Series sections.
- **StatusPanel.xml**: Vertically aligned status metrics with color-coded indicators.
- **RefreshModal.xml**: Spinner + text overlay.
- **Toast.xml**: Small timed message overlay.
- **LoginForm.xml**: Username/password/device code fields + remember toggle.

## 3) Navigation Logic (Remote-Based)

### Global Navigation
- **Back**: Close detail → return to tab content; from tabs → return to splash or exit if at root.
- **OK**: Open detail view or trigger Play/Refresh actions.
- **Left/Right**: Switch tabs when focus is on TabBar; move within row when focus is in RowList.
- **Up/Down**: Navigate between rows in ContentGrid or between fields in LoginForm.

### Tab Focus Rules
- TabBar is first focusable element after entering HomeScene.
- **Right** moves into ContentGrid; **Left** returns to TabBar.
- When switching tabs, preserve last focused row and item per tab (cache focus index by tab).

### Detail View
- **OK** on content item opens DetailView overlay in-place.
- **Back** closes DetailView and restores previous row/item focus.
- **Play** button transitions to PlaybackScene.

### Refresh
- Refresh tab or button: **OK** triggers RefreshModal.
- While refreshing: focus locked to modal, Back disabled to prevent accidental cancellation.
- On completion: dismiss modal, show Toast, update Status tab data.

## 4) UX Improvements Specific to Roku

- **Perceived fast startup**: show Splash immediately and defer network calls until after UI paints; display "Checking account…" after 2–3s if still loading.
- **Focus clarity**: 110–115% scale with glow, and subtle shadow on focused poster for distance viewing.
- **Row memory**: store last focused row/item per tab for quicker return.
- **Predictable Back stack**: consistent exit path (Detail → Content → Tabs → Exit prompt).
- **Smart loading**: show per-row skeleton placeholders instead of full-screen spinners.
- **Safe refresh**: block navigation during refresh and show clear completion toast.
- **Remote ergonomics**: large hit areas, avoid deep nested focus traps.

## 5) State Machines

### 5.1 App Launch State

```
[BOOT]
  -> show SplashView + Spinner
  -> after 2–3s show "Checking account…" if still loading
  -> CredentialCheck
      -> hasCredentials: HomeScene
      -> noCredentials: LoginScene
```

### 5.2 Login State

```
[LOGIN_IDLE]
  -> user inputs or device code
  -> OK on Submit: [LOGIN_AUTH]

[LOGIN_AUTH]
  -> show AuthSpinner
  -> success: store credentials -> HomeScene
  -> error: [LOGIN_ERROR]

[LOGIN_ERROR]
  -> show friendly message
  -> return to [LOGIN_IDLE]
```

### 5.3 Refresh State

```
[REFRESH_IDLE]
  -> OK on Refresh: [REFRESHING]

[REFRESHING]
  -> show RefreshModal
  -> success: update content/status -> [REFRESH_COMPLETE]
  -> error: [REFRESH_ERROR]

[REFRESH_COMPLETE]
  -> show Toast + timestamp
  -> return to [REFRESH_IDLE]

[REFRESH_ERROR]
  -> show ErrorDialog
  -> return to [REFRESH_IDLE]
```

### 5.4 Content Browsing State

```
[CONTENT_IDLE]
  -> Tab focus change: load tab data (if not cached)
  -> Up/Down/Left/Right: focus changes within grid
  -> OK on item: [DETAIL_OPEN]

[DETAIL_OPEN]
  -> show DetailView
  -> OK on Play: [PLAYBACK]
  -> Back: [CONTENT_IDLE]

[PLAYBACK]
  -> PlaybackScene
  -> Back/End: return to [DETAIL_OPEN] or [CONTENT_IDLE] (configurable)
```

## 6) UX Flow Summary (Launch → Home → Content → Playback)

1. **Splash** shows immediately, then checks credentials in registry.
2. **Login** displayed if credentials missing; otherwise go to Home.
3. **Home** opens with TabBar focus; user navigates through tabs and content rows.
4. **Detail** opens in overlay; Play starts PlaybackScene.
5. **Refresh** available via tab or button; shows modal and updates Status.
