import type { ReactNode } from "react";
import Box from "@mui/material/Box";

// the mockup's form row: a small grey label above the control
function Field({ label, children }: { label: string; children: ReactNode }) {
  return (
    <Box component="label" sx={{ display: "grid", gap: 0.5, fontSize: 13, color: "text.secondary" }}>
      {label}
      {children}
    </Box>
  );
}

export default Field;
