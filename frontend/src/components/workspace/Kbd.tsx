import Box from "@mui/material/Box";
import { tokens } from "../../theme";

// a small key hint after a button label, e.g. "Save and next [3]";
// onAccent: drawn on the blue button, so it takes the button's white
function Kbd({ children, onAccent = false }: { children: string; onAccent?: boolean }) {
  return (
    <Box
      component="kbd"
      sx={{
        ml: 0.5,
        px: 0.5,
        fontFamily: "ui-monospace, Menlo, monospace",
        fontSize: 11,
        lineHeight: 1.4,
        borderRadius: "4px",
        border: `0.5px solid ${onAccent ? "currentColor" : tokens.borderStrong}`,
        color: onAccent ? "inherit" : tokens.textSecondary,
      }}
    >
      {children}
    </Box>
  );
}

export default Kbd;
