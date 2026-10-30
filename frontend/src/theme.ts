import { createTheme } from "@mui/material/styles";

// The look of the approved mockups: a warm off-white page, white cards with
// hairline borders, one blue for the main action, and two font weights (400, 500).
// Components that need a value MUI's palette has no slot for read it from here.
export const tokens = {
  page: "#F5F4EF",
  card: "#FFFFFF",
  subtle: "#F0EEE6",
  border: "rgba(31, 30, 29, 0.15)",
  borderStrong: "rgba(31, 30, 29, 0.3)",
  text: "#141413",
  textSecondary: "#5E5D59",
  textMuted: "#87867F",
  accent: "#2775C7",
  accentHover: "#1F62A8",
  accentBg: "#E6F1FB",
  accentText: "#185FA5",
  accentBorder: "#85B7EB",
  danger: "#A32D2D",
  marked: "#EF9F27",
  accepted: "#7F77DD",
};

const hairline = `0.5px solid ${tokens.border}`;
const hairlineStrong = `0.5px solid ${tokens.borderStrong}`;

export const theme = createTheme({
  palette: {
    primary: { main: tokens.accent, dark: tokens.accentHover, contrastText: "#FFFFFF" },
    error: { main: tokens.danger },
    text: { primary: tokens.text, secondary: tokens.textSecondary, disabled: tokens.textMuted },
    divider: tokens.border,
    background: { default: tokens.page, paper: tokens.card },
  },
  shape: { borderRadius: 8 },
  typography: {
    fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", system-ui, sans-serif',
    fontSize: 14,
    fontWeightRegular: 400,
    fontWeightMedium: 500,
    fontWeightBold: 500,
    h5: { fontSize: 20, fontWeight: 500, lineHeight: 1.3 },
    h6: { fontSize: 15, fontWeight: 500, lineHeight: 1.4 },
    subtitle1: { fontSize: 14, fontWeight: 500, lineHeight: 1.5 },
    subtitle2: { fontSize: 13, fontWeight: 500, lineHeight: 1.5 },
    body1: { fontSize: 14, lineHeight: 1.6 },
    body2: { fontSize: 13, lineHeight: 1.5 },
    caption: { fontSize: 12, lineHeight: 1.5 },
    // MUI uppercases button labels by default; the spec wants sentence case
    button: { fontSize: 14, fontWeight: 400, textTransform: "none" },
  },
  components: {
    MuiButtonBase: { defaultProps: { disableRipple: true } },
    MuiCard: {
      defaultProps: { variant: "outlined" },
      styleOverrides: { root: { borderRadius: 12, border: hairline } },
    },
    MuiButton: {
      defaultProps: { disableElevation: true },
      styleOverrides: {
        root: { borderRadius: 8, minHeight: 36, padding: "0 14px", transition: "transform 0.1s", "&:active": { transform: "scale(0.98)" } },
        outlined: {
          border: hairlineStrong,
          color: tokens.text,
          "&:hover": { border: hairlineStrong, backgroundColor: tokens.subtle },
        },
        contained: { "&:hover": { backgroundColor: tokens.accentHover } },
        sizeSmall: { minHeight: 28, padding: "0 10px", fontSize: 12 },
      },
    },
    MuiOutlinedInput: {
      styleOverrides: {
        root: {
          borderRadius: 8,
          backgroundColor: tokens.card,
          fontSize: 14,
          "& .MuiOutlinedInput-notchedOutline": { border: hairlineStrong },
          "&:hover .MuiOutlinedInput-notchedOutline": { borderColor: tokens.textMuted },
          "&.Mui-focused .MuiOutlinedInput-notchedOutline": { border: `1px solid ${tokens.accent}` },
          "&.Mui-error .MuiOutlinedInput-notchedOutline": { border: `1px solid ${tokens.danger}` },
        },
        // 8px + 20px line + 8px = the mockup's 36px field
        input: { padding: "8px 12px", height: 20 },
      },
    },
    MuiSelect: { styleOverrides: { select: { minHeight: 20 } } },
    MuiLinearProgress: {
      styleOverrides: {
        root: { height: 6, borderRadius: 3, backgroundColor: tokens.border },
        bar: { borderRadius: 3, backgroundColor: tokens.accent },
      },
    },
    MuiIconButton: { styleOverrides: { root: { color: tokens.textSecondary, borderRadius: 6 } } },
    MuiDialog: {
      styleOverrides: { paper: { borderRadius: 12, border: hairline, boxShadow: "none" } },
    },
    // dropdown menus: a hairline and a soft shadow instead of MUI's heavy elevation
    MuiPopover: {
      styleOverrides: { paper: { borderRadius: 8, border: hairline, boxShadow: "0 8px 24px rgba(0, 0, 0, 0.08)" } },
    },
  },
});
