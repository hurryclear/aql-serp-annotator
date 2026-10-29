import Box from "@mui/material/Box";

// a small key hint after a button label, e.g. "Save and next [3]"
function Kbd({ children }: { children: string }) {
  return (
    <Box
      component="kbd"
      sx={{ ml: 0.75, px: 0.5, fontFamily: "monospace", fontSize: 11, lineHeight: 1.5, border: 1, borderColor: "divider", borderRadius: 0.5, opacity: 0.8 }}
    >
      {children}
    </Box>
  );
}

export default Kbd;
