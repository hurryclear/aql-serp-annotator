import { createTheme } from "@mui/material/styles";

// the one place both pages take their look from: colours, corners, button style
export const theme = createTheme({
  palette: {
    background: { default: "#f4f4f2", paper: "#ffffff" },
  },
  shape: { borderRadius: 8 },
  typography: {
    // MUI uppercases button labels by default; the spec wants sentence case
    button: { textTransform: "none" },
  },
  components: {
    MuiButton: { defaultProps: { disableElevation: true } },
    MuiCard: { defaultProps: { variant: "outlined" } },
  },
});
