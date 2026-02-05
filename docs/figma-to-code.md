# Figma to Code Integration Notes

The web frontend is generated from Figma Make and lives in `frontend-web/src`. The app is organized to keep Figma output intact while layering API and navigation logic on top.

## Integration Guidelines

- Keep generated components in `src/components` and screens in `src/screens`.
- Add API calls through `src/services/api.ts` and UI hooks in `src/hooks/`.
- Avoid coupling Streamlit with the user-facing experience.
- Keep focus styles and remote-friendly navigation when adding new components.

## Environment

Configure the backend URL via `VITE_API_BASE_URL` in `frontend-web/.env`.
